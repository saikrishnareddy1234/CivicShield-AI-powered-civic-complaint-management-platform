import os
from groq import Groq


client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)


response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": "Classify this civic problem: There is garbage overflowing near a school."
        }
    ],
    temperature=0
)


print(response.choices[0].message.content)