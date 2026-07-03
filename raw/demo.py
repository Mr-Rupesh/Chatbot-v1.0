import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant."
    }
]

print("Groq Chatbot")
print("Type 'exit' to quit.\n")

while True:
    user = input("You: ")

    if user.lower() == "exit":
        break

    messages.append({
        "role": "user",
        "content": user
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
    )

    reply = response.choices[0].message.content

    print(f"Bot: {reply}\n")

    messages.append({
        "role": "assistant",
        "content": reply
    })