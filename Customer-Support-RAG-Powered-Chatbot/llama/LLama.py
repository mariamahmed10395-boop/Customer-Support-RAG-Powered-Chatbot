import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_answer(context, question):
    
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
    )

    return chat_completion.choices[0].message.content