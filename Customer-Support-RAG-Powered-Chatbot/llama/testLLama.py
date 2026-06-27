from LLama import generate_answer

context = """
سياسة الشركة تسمح بإلغاء الطلب خلال 24 ساعة.
"""

question = "هل يمكنني إلغاء الطلب؟"

answer = generate_answer(context, question)

print(answer)