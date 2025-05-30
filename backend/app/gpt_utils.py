from openai import OpenAI
import os
import json
from dotenv import load_dotenv
load_dotenv()
from app.utils import normalize_type, normalize_profile, normalize_genre
import html


print("DEBUG: ENV KEY =", os.getenv("OPENAI_API_KEY"))
client = OpenAI(
    base_url="https://api.together.xyz/v1",  # You can still use Together
)

#openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_feedback_prompt(genre: str, subgenre: str, type: str, analysis_data: dict, feedback_profile: str) -> str:
    # Normalize and sanitize inputs
    type = normalize_type(type)
    genre = normalize_genre(genre)
    feedback_profile = normalize_profile(feedback_profile)
    subgenre = subgenre.strip().title() if subgenre else ""

    role_context = {
        "mixdown": f"You are a professional **mixing engineer reviewing a mixdown** with deep knowledge of {genre} music, and especially {subgenre} music.",
        "mastering": f"You are a professional **mastering engineer giving mastering advice** for this mixdown with deep knowledge of {genre} music, and especially {subgenre} music.",
        "master": f"You are a professional **mastering engineer reviewing a finished master** to assess its quality with deep knowledge of {genre} music, and especially {subgenre} music.",
    }

    profile_guidance = {
        "simple": (
            "Speak as if you're explaining to someone with no technical knowledge. "
            "Avoid all audio engineering jargon. "
            "Use plain, friendly language like 'the bass feels too strong' or "
            "'maybe turn the drums down a bit'. Focus on what to do, not how."
        ),
        "detailed": (
            "Use moderately technical language. "
            "Assume the listener has some production experience. "
            "You can mention terms like EQ, compression, reverb, etc., "
            "but keep explanations short and accessible."
        ),
        "pro": (
            "Use advanced audio production vocabulary. "
            "Assume you're speaking to a seasoned engineer. "
            "Feel free to reference techniques like transient shaping, mid-side EQ, multiband compression, etc. "
            "Keep your tone concise and precise."
        )
    }

    context = role_context.get(type, f"You are an audio engineer for {genre} music, and especially {subgenre} music.")
    skill_hint = profile_guidance.get(feedback_profile, "")

    peak_warning = ""
    if analysis_data.get("peak_issue_explanation"):
        peak_warning = f"\n⚠️ Peak warning: {analysis_data['peak_issue_explanation']}\n"

    return f"""
    {context}

    {skill_hint}

    This is an analysis of the track's {type} version:
    - Peak: {analysis_data['peak_db']} dB
    - RMS Avg: {analysis_data['rms_db_avg']} dB
    - RMS Peak: {analysis_data['rms_db_peak']} dB
    - LUFS: {analysis_data['lufs']}
    - Avg Transient Strength: {analysis_data['avg_transient_strength']}
    - Max Transient Strength: {analysis_data['max_transient_strength']}
    - Transients: {analysis_data['transient_description']}
    - Spectral balance note: {analysis_data['spectral_balance_description']}
    - Dynamic range: {analysis_data['dynamic_range']}
    - Stereo width: {analysis_data['stereo_width']}
    - Key: {analysis_data['key']}
    - Tempo: {analysis_data['tempo']} BPM
    - Bass profile: {analysis_data['bass_profile']} ({analysis_data['low_end_energy_ratio']})
      {analysis_data.get('low_end_description', '')}
    - Band energies: {json.dumps(analysis_data['band_energies'], indent=2)}
    {peak_warning}

    Your task:
    Consider **especially** the relationship between role context and genre/subgenre.

    Return exactly 2–3 bullet points, each one should:
    - Identify 1 issue clearly
    - Give a **concrete, genre-aware** improvement tip
    - Briefly explain **why** this advice helps, referencing the data or genre
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
    # Sanitize follow-up question
    user_question = user_question.strip()
    user_question = user_question.replace("\n", " ")  # avoid prompt injection tricks
    user_question = html.escape(user_question)[:300]  # escape HTML and truncate

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

