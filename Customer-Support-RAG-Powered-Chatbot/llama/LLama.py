import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_answer(context, question):

    prompt = f"""
    أنت مساعد ذكي لخدمة العملاء.

    اعتمد فقط على المعلومات التالية:
    {context}

    السؤال:
    {question}

    إذا لم تجد الإجابة داخل المعلومات لا تخترع معلومات.
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