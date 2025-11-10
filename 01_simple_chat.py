import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Why sky is blue?"}
    ]
)
answer = response.choices[0].message.content
print("Assistant:", answer)
