import os
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# Configure paths so the Graph can access the main app.py file correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Define the Graph State
class BasmalaGraphState(TypedDict):
    query: str
    category_filter: str
    top_k: int
    context_str: str
    response: str
    sources: list


# 2. Data Retrieval Node (calls the team's semantic search function)
def graph_retrieve_node(state: BasmalaGraphState):
    print("\n[LangGraph Node] >>> Retrieving relevant documents from the FAISS index...")

    # Import the semantic search function from the main app
    from app import get_semantic_search_results

    results = get_semantic_search_results(
        state["query"],
        state["category_filter"],
        state["top_k"]
    )

    if results:
        context_blocks = []
        for i, res in enumerate(results, 1):
            context_blocks.append(
                f"Document [{i}]:\n"
                f"Category: {res['category']} | Intent: {res['intent']}\n"
                f"Customer Question: {res['instruction']}\n"
                f"Support Answer: {res['response']}"
            )
        context_str = "\n\n---\n\n".join(context_blocks)
    else:
        context_str = (
            "No relevant customer support documents were found for this query."
        )

    return {
        "context_str": context_str,
        "sources": results
    }


# 3. Response Generation Node (connects to the Groq LLM)
def graph_generate_node(state: BasmalaGraphState):
    print("\n[LangGraph Node] >>> Generating the final response using Llama-3...")

    # Import the Groq client and system prompt from the main app
    from app import groq_client, SYSTEM_PROMPT

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT.format(
                        context=state["context_str"]
                    ),
                },
                {
                    "role": "user",
                    "content": state["query"],
                }
            ],
            model="llama3-8b-8192",
            temperature=0.2,
            max_tokens=1024,
        )

        generated_response = (
            chat_completion.choices[0].message.content
        )

    except Exception as e:
        print(f"[LangGraph Error] Failed to generate response: {e}")
        generated_response = (
            "An error occurred while generating the response."
        )

    return {"response": generated_response}


# 4. Build and compile the LangGraph workflow
builder = StateGraph(BasmalaGraphState)

builder.add_node("retrieve_data_step", graph_retrieve_node)
builder.add_node("generate_answer_step", graph_generate_node)

builder.add_edge(START, "retrieve_data_step")
builder.add_edge("retrieve_data_step", "generate_answer_step")
builder.add_edge("generate_answer_step", END)

# Final compiled graph imported by the main app
customer_rag_graph = builder.compile()