import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Initialize the Groq client
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_answer(context, question):
    """
    Generates a response using Groq LLM strictly based on the provided context.
    """
    prompt = f"""
    You are an intelligent customer support assistant.

    Strictly rely ONLY on the following provided context to answer the user's question. Do not assume or extrapolate any information outside of this context.

    Context:
    {context}

    User Question:
    {question}

    If the answer cannot be found within the context, reply with: "I'm sorry, I cannot find this information." Do not hallucinate or make up facts.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.2,  # Added to ensure strict adherence to context and high accuracy
        max_tokens=1024   # Optional: limits response length to optimize token usage
    )

    return chat_completion.choices[0].message.content