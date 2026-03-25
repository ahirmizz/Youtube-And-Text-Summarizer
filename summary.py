import os
from groq import Groq

def summarize_text(text):
    """Generates a concise summary of input text using the Groq LLM API."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY")
    
    client = Groq(api_key=api_key)

    prompt = f"""
Write a clear, concise summary of the text below.

The summary should:
- Include the main goal
- Mention the key conflict or challenge
- Explain the outcome
- State the overall message or theme

Write in English.
Keep it to one short paragraph.
Do not add extra commentary.

Text:
{text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content