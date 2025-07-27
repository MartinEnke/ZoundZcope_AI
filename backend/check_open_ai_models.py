from dotenv import load_dotenv
load_dotenv()

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
models = client.models.list()
print([model.id for model in models.data])


# python backend/check_open_ai_models.py