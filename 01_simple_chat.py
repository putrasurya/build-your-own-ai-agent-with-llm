import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

def simple_chat(prompt):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Why sky is blue?"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    user_prompt = "Explain the theory of relativity in simple terms."
    answer = simple_chat(user_prompt)
    print("Assistant:", answer)