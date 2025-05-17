import openai
import os
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_feedback_prompt(genre: str, analysis_data: dict) -> str:
    return f"""
You're a professional mixing and mastering engineer with deep knowledge of {genre} music.
Here's the analysis of my track. Please give 2–3 concise suggestions on what could be improved,
based on the genre’s standards and common practices.

Analysis:
{json.dumps(analysis_data, indent=2)}

Please respond with a list of issues and improvement tips.
"""

def generate_feedback_response(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]