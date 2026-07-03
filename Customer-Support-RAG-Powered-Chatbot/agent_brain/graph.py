import os
import sys
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Configure paths so the Graph can access the main app.py file correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Define the Graph State
class AgentGraphState(TypedDict):
    query: str
    category_filter: str
    top_k: int
    context_str: str
    response: str
    sources: list
    messages: Annotated[Sequence[BaseMessage], add_messages] # Tracks session chat history dynamically
    transfer_to_human: bool # Flag to signal human agent intervention


# 2. Data Retrieval Node
def graph_retrieve_node(state: AgentGraphState):
    print("\n[LangGraph Node] >>> Retrieving relevant documents from the FAISS index...")
    try:
        from retriever import get_relevant_context
        retrieved_context = get_relevant_context(query=state["query"], k=3)
    except Exception as e:
        print(f"[LangGraph Error] Failed during data retrieval step: {e}")
        retrieved_context = ""

    return {
        "context_str": retrieved_context,
        "sources": [retrieved_context] if retrieved_context else []
    }

# 3. Response Generation Node 
def graph_generate_node(state: AgentGraphState):
    print("\n[LangGraph Node] >>> Generating the final response using Llama-3...")
    from app import groq_client
    from langchain_core.messages import HumanMessage, AIMessage

    # ── Strict RAG Guardrail Prompt ──────────────────────────────────────────
    # This prompt enforces that the LLM ONLY answers from retrieved context.
    # Out-of-domain queries receive a polite, standardised refusal rather than
    # a hallucinated or general-knowledge answer.
    # ─────────────────────────────────────────────────────────────────────────
    FLEXIBLE_PROMPT = """You are a precise, professional AI Assistant for the CoreAI Knowledge Base system.
Your ONLY source of truth is the "Retrieved Context" section provided below, which contains excerpts
from documents indexed in the workspace (e.g., HR Policies, Project Scopes, Support Data).

═══════════════════════════════════════════════════════
STRICT RAG GUARDRAIL RULES — READ CAREFULLY:
═══════════════════════════════════════════════════════

RULE 1 — GROUNDING:
  Answer EXCLUSIVELY using information found in the Retrieved Context below.
  Do NOT use any prior training knowledge, general world knowledge, or assumptions
  that are not explicitly supported by the provided context.

RULE 2 — OUT-OF-DOMAIN REFUSAL:
  If the user's question cannot be answered using the Retrieved Context
  (e.g., the context contains HR Policies but the user asks about booking food,
  or the context contains project scopes but the user asks about weather),
  you MUST respond with EXACTLY this message and nothing else:

    "I cannot find any information regarding this in the uploaded CoreAI Knowledge Base documents.
     Currently, my knowledge is limited to the active files listed in your workspace panel
     (e.g., HR Policies, Project Scopes, Support Data). Please rephrase your question
     to relate to the available indexed documents."

  Arabic equivalent (use when user writes in Arabic):
    "لا يمكنني العثور على أي معلومات تتعلق بهذا في مستندات قاعدة معرفة CoreAI المُحمَّلة.
     حاليًا، تقتصر معرفتي على الملفات النشطة المدرجة في لوحة مساحة العمل الخاصة بك
     (مثل سياسات الموارد البشرية، ونطاقات المشاريع، وبيانات الدعم).
     يُرجى إعادة صياغة سؤالك ليكون متعلقًا بالمستندات المفهرسة المتاحة."

RULE 3 — LANGUAGE MATCHING:
  Detect the language of the user's question and respond in that SAME language.
  If the user writes in Arabic → translate the context answer into fluent Arabic.
  If the user writes in English → respond in English.
  If the context is in English but the user writes in Arabic, translate the answer.

RULE 4 — SOURCE CITATION:
  When you successfully answer a question from the context, end your response with
  a single line in this exact format:
    📄 Source: [document name or topic from context] | Confidence: [High / Medium / Low]

RULE 5 — NO HALLUCINATION TOLERANCE:
  If you are uncertain or the context only partially answers the question,
  state clearly what you found and what was not available.
  NEVER invent facts, statistics, names, dates, or policies.

═══════════════════════════════════════════════════════
Retrieved Context (your ONLY allowed source of truth):
═══════════════════════════════════════════════════════
{context}
"""


    try:
        full_messages = [
            {
                "role": "system",
                "content": FLEXIBLE_PROMPT.format(context=state.get("context_str", "")),
            }
        ]
        
        if "messages" in state and len(state["messages"]) > 0:
            for msg in state["messages"]:
                if msg.type == "human":
                    full_messages.append({"role": "user", "content": msg.content})
                elif msg.type == "ai":
                    full_messages.append({"role": "assistant", "content": msg.content})
            
            if full_messages[-1]["content"] != state["query"]:
                full_messages.append({"role": "user", "content": state["query"]})
        else:
            
            full_messages.append({"role": "user", "content": state["query"]})

        chat_completion = groq_client.chat.completions.create(
            messages=full_messages,
            model="llama-3.1-8b-instant",  
            temperature=0.0,  
            max_tokens=1024,
        )

        generated_response = chat_completion.choices[0].message.content

    except Exception as e:
        print(f"[LangGraph Error] Failed to generate response: {e}")
        generated_response = "An error occurred while generating the response."

    new_messages = []
    
    if "messages" not in state or len(state["messages"]) == 0:
        new_messages.append(HumanMessage(content=state["query"]))
    
    new_messages.append(AIMessage(content=generated_response))

    return {
        "response": generated_response,
        "messages": new_messages
    }
    
# 4. Conditional Router to assess model confidence
def check_if_human_needed(state: AgentGraphState):
    response_text = state.get("response", "").lower().strip()

    # Match the exact refusal phrases from the updated RAG guardrail prompt
    out_of_domain_signals = [
        "cannot find any information regarding this",     # English refusal
        "لا يمكنني العثور على أي معلومات",               # Arabic refusal
        "an error occurred while generating",            # Technical errors
    ]

    if any(signal in response_text for signal in out_of_domain_signals):
        print("\n[LangGraph Router] >>> Out-of-domain or error detected. Routing to Human Handoff...")
        return "transfer"

    print("\n[LangGraph Router] >>> Response verified from context. Ending workflow.")
    return "end"


# 5. Human Handoff Node
def graph_human_handoff_node(state: AgentGraphState):
    print("\n[LangGraph Node] >>> Activating the Human Handoff Flag...")
    return {"transfer_to_human": True}


# 6. Build and compile the LangGraph workflow
builder = StateGraph(AgentGraphState)

builder.add_node("retrieve_data_step", graph_retrieve_node)
builder.add_node("generate_answer_step", graph_generate_node)
builder.add_node("human_handoff_step", graph_human_handoff_node)

builder.add_edge(START, "retrieve_data_step")
builder.add_edge("retrieve_data_step", "generate_answer_step")

builder.add_conditional_edges(
    "generate_answer_step",
    check_if_human_needed,
    {
        "transfer": "human_handoff_step",
        "end": END
    }
)

builder.add_edge("human_handoff_step", END)

memory = MemorySaver()
customer_rag_graph = builder.compile(checkpointer=memory)