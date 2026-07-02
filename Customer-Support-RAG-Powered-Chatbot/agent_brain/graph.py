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

    FLEXIBLE_PROMPT = """You are an advanced multilingual customer support AI assistant. 
Your task is to answer the user's current question using ONLY the retrieved context provided below.

CRITICAL RULES:
1. If the context contains relevant information, answer the user's question directly and professionally.
2. LANGUAGE MATCHING: Respond in the SAME language the user used to ask their question. If the user asks in Arabic, read the English context, translate the answer, and respond in fluent Arabic. If they ask in English, respond in English.
3. If the context is completely irrelevant to the current question (e.g., asking about Mars or space), you MUST reply with exactly:
   - In English: "I cannot find this information in my database."
   - In Arabic: "لا يمكنني العثور على هذه المعلومات في قاعدة البيانات الخاصة بي."
4. Do not reuse previous answers if they do not match the current query.

Retrieved Context:
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
    
    if "cannot find this information" in response_text or "لا يمكنني العثور" in response_text or "database" in response_text:
        print("\n[LangGraph Router] >>> Confidence score low! Routing to Human Handoff...")
        return "transfer"
    
    print("\n[LangGraph Router] >>> Response verified successfully. Ending workflow.")
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