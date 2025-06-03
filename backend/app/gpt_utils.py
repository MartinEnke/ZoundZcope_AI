from openai import OpenAI
import os
import json
from dotenv import load_dotenv
load_dotenv()
from app.utils import normalize_type, normalize_profile, normalize_genre, ALLOWED_GENRES, normalize_subgenre
import html


print("DEBUG: ENV KEY =", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# client = OpenAI(
#     base_url="https://api.together.xyz/v1",  # You can still use Together
# )

#openai.api_key = os.getenv("OPENAI_API_KEY")

# 1. Role Contexts (based on type)
ROLE_CONTEXTS = {
    "mixdown": "You are a professional **mixing engineer reviewing a mixdown** with deep knowledge of {genre}, especially {subgenre}.",
    "mastering": "You are a professional **mastering engineer giving mastering advice** for this mixdown with deep knowledge of {genre}, especially {subgenre}.",
    "master": "You are a professional **mastering engineer reviewing a finished master** to assess its quality with deep knowledge of {genre}, especially {subgenre}.",
}

# 2. Profile Guidance
PROFILE_GUIDANCE = {
    "simple": (
        "Speak as if you're explaining to someone with no technical knowledge. "
        "Avoid all audio engineering jargon. "
        "Use plain, friendly language like 'the bass feels too strong'. Focus on what to do, not how."
    ),
    "detailed": (
        "Use moderately technical language. "
        "Assume the listener has some production experience. "
        "You can mention EQ, compression, reverb, etc., but keep explanations short and accessible."
    ),
    "pro": (
        "Use advanced audio production vocabulary. "
        "Assume you're speaking to a seasoned engineer. "
        "Feel free to reference techniques like mid-side EQ, transient shaping, etc. Keep it precise and focused."
    ),
}


def generate_feedback_prompt(genre: str, subgenre: str, type: str, analysis_data: dict, feedback_profile: str) -> str:
    type = normalize_type(type)
    if type not in ROLE_CONTEXTS:
        raise ValueError(f"Unknown type: {type}")
    genre = normalize_genre(genre)
    if genre not in ALLOWED_GENRES:
        raise ValueError(f"Unknown genre: {genre}")
    subgenre = normalize_subgenre(subgenre)
    feedback_profile = normalize_profile(feedback_profile)
    if feedback_profile not in PROFILE_GUIDANCE:
        raise ValueError(f"Unknown feedback_profile: {feedback_profile}")


    context = ROLE_CONTEXTS[type].format(genre=genre, subgenre=subgenre)
    skill_hint = PROFILE_GUIDANCE.get(feedback_profile, "")

    peak_warning = ""
    if analysis_data.get("peak_issue_explanation"):
        peak_warning = f"\n⚠️ Peak warning: {analysis_data['peak_issue_explanation']}\n"

    # Final assembly
    return f"""
### Context
{context}

### Communication Style
{skill_hint}

### Track Analysis Data
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

### Instructions
Return exactly 2–3 bullet points, each of which must:
- Identify one clear issue
- Suggest a **genre-aware**, specific improvement
- Briefly explain **why** the advice is useful, referencing the data or genre
- Use 2–3 sentences per bullet point

⚠️ Do not include a title, greeting, summary, or closing line.
### Format
Each bullet must follow this structure:
- **Issue**: Clearly state what stands out and why it's important
- **Improvement**: Offer a specific tip, ideally with plugin/method suggestions
- Keep each bullet short and focused (2–3 sentences)

"""


def generate_feedback_response(prompt: str) -> str:
    print("🔍 Prompt being sent to GPT:\n", prompt)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    # response = client.chat.completions.create(
    #     model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    #     messages=[{"role": "user", "content": prompt}]
    # )
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

