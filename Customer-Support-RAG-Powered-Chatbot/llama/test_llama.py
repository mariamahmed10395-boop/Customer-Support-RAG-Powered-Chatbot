from LLama import generate_answer

context = "The company policy allows order cancellation within 24 hours."
question = "Can I cancel my order?"

answer = generate_answer(context, question)

print(answer)