from groq import Groq

# API KEY
client = Groq(
    api_key=""
)

# Context وهمي
context = """
سياسة الشركة تسمح بإلغاء الطلب خلال 24 ساعة.
"""

# سؤال المستخدم
question = "هل يمكنني إلغاء الطلب؟"

# Prompt
prompt = f"""
أنت مساعد ذكي لخدمة العملاء.

اعتمد فقط على المعلومات التالية:
{context}

السؤال:
{question}

إذا لم تجد الإجابة داخل المعلومات لا تخترع معلومات.
"""

# إرسال الطلب للموديل
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
    model="llama3-8b-8192",
)

# طباعة الرد
print(chat_completion.choices[0].message.content)