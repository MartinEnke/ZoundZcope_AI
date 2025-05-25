from openai import OpenAI
import os
import json
from dotenv import load_dotenv
load_dotenv()

print("DEBUG: ENV KEY =", os.getenv("OPENAI_API_KEY"))
client = OpenAI(
    base_url="https://api.together.xyz/v1",  # You can still use Together
)

#openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_feedback_prompt(genre: str, type: str, analysis_data: dict, feedback_profile: str) -> str:
    role_context = {
        "mixdown": f"You are a professional **mixing engineer** with deep knowledge of {genre} music.",
        "master": f"You are a professional **mastering engineer** with deep knowledge of {genre} music.",
    }

    profile_guidance = {
        "simple": "Use beginner-friendly language. Avoid technical jargon. Give practical advice like 'try boosting bass by 3dB'.",
        "detailed": "Use moderately technical language. Assume some production experience. Include brief explanations like 'try gentle saturation to add presence'.",
        "pro": "Use professional-level language. Assume expert knowledge. Provide detailed, technical tips using terms like multiband compression, stereo field manipulation, and transient shaping."
    }

    context = role_context.get(type.lower(), f"You are an audio engineer for {genre} music.")
    skill_hint = profile_guidance.get(feedback_profile.lower(), "")

    return f"""
    {context}

    {skill_hint}

    This is an analysis of the track's {type} version:
    - Peak: {analysis_data['peak_db']} dB
    - RMS: {analysis_data['rms_db']} dB
    - LUFS: {analysis_data['lufs']}
    - Dynamic range: {analysis_data['dynamic_range']}
    - Stereo width: {analysis_data['stereo_width']}
    - Key: {analysis_data['key']}
    - Tempo: {analysis_data['tempo']} BPM
    - Bass profile: {analysis_data['bass_profile']}
    - Band energies: {json.dumps(analysis_data['band_energies'], indent=2)}

    Your task:
    Return **exactly 2–3 bullet points**, each one should:
    - Identify 1 issue clearly
    - Give a **concrete, genre-aware** improvement tip
    - Keep each bullet to 2–3 sentences

    Only return the bullet points in a clean, readable format.
    """


def generate_feedback_response(prompt: str) -> str:
    print("🔍 Prompt being sent to GPT:\n", prompt)
    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def generate_followup_response(analysis_text: str, feedback_text: str, user_question: str) -> str:
    combined_prompt = f"""
You are an expert audio engineer assistant.

Here is the previous analysis of the track:
{analysis_text}

Here is the feedback that was given:
{feedback_text}

Now the user has a follow-up question:
"{user_question}"

Please answer helpfully and concisely, using the context above.
Avoid repeating the full analysis or feedback again.
"""
    print("💬 Sending follow-up prompt:\n", combined_prompt)

    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": combined_prompt}]
    )
    return response.choices[0].message.content.strip()

