import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_ENDPOINT = os.getenv("OPENROUTER_ENDPOINT")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")

client = OpenAI(
  base_url=OPENROUTER_ENDPOINT,
  api_key=OPENROUTER_API_KEY,
)

completion = client.chat.completions.create(
    model=OPENROUTER_MODEL,
    messages=[
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": "Write a one-sentence bedtime story about a unicorn."
            }
          ]
        }
      ]
)

print(completion.choices[0].message.content)
