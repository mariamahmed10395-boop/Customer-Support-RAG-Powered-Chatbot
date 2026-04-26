import pandas as pd

# 1. قراءة الملف
df = pd.read_csv(r'C:\Users\modern\OneDrive\Desktop\Customer-Support-RAG-Powered-Chatbot\Customer-Support-RAG-Powered-Chatbot\Data_Preprocessing\customer_support_data.csv')

# 2. استكشاف أول 5 صفوف لنفهم شكل البيانات
print(df.head())

# 3. معرفة أسماء الأعمدة ونوع البيانات
print(df.info())

# حذف أي صف يحتوي على قيم فارغة في الأعمدة الأساسية
df = df.dropna(subset=['instruction', 'response'])

# حذف الصفوف المكررة تماماً
df = df.drop_duplicates()
#عدد الصفوف بعد التنظيف
print(f" {len(df)}")

import re

def clean_text(text):
    text = text.lower()
    text = text.replace("{{order number}}", "[order number]")
    text = text.replace("{{refund amount}}", "[refund amount]")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['instruction'] = df['instruction'].apply(clean_text)
df['response'] = df['response'].apply(clean_text)

# دمج الأعمدة في عمود واحد يسمى 'context'
df['context'] = "Intent: " + df['intent'] + " | Question: " + df['instruction'] + " | Answer: " + df['response']

# عرض مثال لشكل المعلومة بعد الدمج
print(df['context'].iloc[0])

df.to_csv('processed_support_data.csv', index=False)