from openai import OpenAI
import os
import json
from dotenv import load_dotenv
load_dotenv()
from app.utils import normalize_type, normalize_profile, normalize_genre, ALLOWED_GENRES, normalize_subgenre
import html
import re


print("DEBUG: ENV KEY =", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# client = OpenAI(
#     base_url="https://api.together.xyz/v1",  # You can still use Together
# )

#openai.api_key = os.getenv("OPENAI_API_KEY")


ROLE_CONTEXTS = {
    "mixdown": "You are a professional **mixing engineer reviewing a mixdown** with deep knowledge of {genre}, especially {subgenre}.",
    "mastering": "You are a professional **mastering engineer giving mastering advice** for this mixdown with deep knowledge of {genre}, especially {subgenre}.",
    "master": "You are a professional **mastering engineer reviewing a finished master** to assess its quality with deep knowledge of {genre}, especially {subgenre}.",
}

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

TONE_REMINDER = {
    "simple": "Your tone should be friendly and intuitive, like explaining music to a curious beginner.",
    "detailed": "Your tone should assume basic knowledge of audio production and be slightly technical but still accessible.",
    "pro": "Your tone should be professional and technical, assuming deep expertise in music production.",
}

FORMAT_RULES = {
    "simple": """
Each bullet must:
- Start with **"Issue"**: Describe in plain language what feels off or unusual in the sound.
- Follow with **"Improvement"**: Suggest a simple, actionable fix without technical terms.
- Use 1–2 short, friendly sentences.
- Briefly say why the suggestion might help, using intuitive, listener-friendly terms.
""",

    "detailed": """
Each bullet must:
- Begin with **"Issue"**: Describe a clear mix/mastering issue using basic production terms.
- Follow with **"Improvement"**: Suggest an actionable tip (e.g., EQ, reverb, compression) with a short reason why.
- Use 2–3 clear sentences.
- Reference analysis data or genre norms when helpful.
""",

    "pro": """
Each bullet must:
- Start with **"Issue"**: Use technical language to precisely identify the issue.
- Follow with **"Improvement"**: Provide a targeted, technique-based recommendation (e.g., transient shaping, multiband sidechaining).
- Keep it sharp and focused: 2–3 dense, information-rich sentences.
- Justify the advice based on analysis or genre expectations.
"""
}

EXAMPLE_OUTPUTS = {
    "simple": """
#### Example Output:
- **Issue**: The bass is too loud and makes the track feel heavy.
  **Improvement**: Turn the bass down a little and check how it sounds with vocals. 
  This will help make everything clearer.

- **Issue**: The sound is too crowded.
  **Improvement**: Try making some sounds quieter or move them left and right. 
  This can make the track feel more open.
""",

    "detailed": """
#### Example Output:
- **Issue**: The RMS Level doesn't match the standard for a mixdown of this {genre}.  
  **Improvement**: Aim for around -15 dB RMS to preserve headroom for mastering. 
  This helps the final master stay loud and punchy, especially in {subgenre}.
  
- **Issue**: The kick and bass are clashing in the low end.
  **Improvement**: Use EQ to reduce overlapping frequencies and sidechain the bass to the kick. 
  This adds clarity to your low end.

- **Issue**: The vocals feel buried in the mix.
  **Improvement**: Add light compression and EQ boost around 2-4 kHz to bring them forward without sounding harsh.
""",

    "pro": """
#### Example Output:
- **Issue**: The RMS Level doesn't match the standard for a master of this {genre}.  
  **Improvement**: Aim for around -8 dB RMS to achieve {genre} typical loudness. 
  This helps the final master stay loud and punchy, especially in {subgenre}.
  
- **Issue**: Excessive buildup around 100Hz is causing low-end smearing.
  **Improvement**: Use a dynamic EQ or sidechain-triggered low-shelf cut on the bass. 
  This maintains punch while improving definition.

- **Issue**: The stereo image collapses in the high-mids.
  **Improvement**: Use mid-side EQ or widening tools (e.g. MicroShift) to open up the 2–6 kHz range. 
  Essential for clarity in {subgenre} arrangements.
"""
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
    communication_style = PROFILE_GUIDANCE[feedback_profile]

    peak_warning = ""
    if analysis_data.get("peak_issue_explanation"):
        peak_warning = f"\n⚠️ Peak warning: {analysis_data['peak_issue_explanation']}\n"

    tone_reminder = TONE_REMINDER.get(feedback_profile, "")
    format_rule = FORMAT_RULES.get(feedback_profile, FORMAT_RULES["detailed"])

    example_output = EXAMPLE_OUTPUTS.get(feedback_profile, "")

    # Final assembly
    return f"""
### Context
{context}

### Communication Style
{communication_style}

### Track Analysis Data
- Peak: {analysis_data['peak_db']} dB
- RMS Peak: {analysis_data['rms_db_peak']} dB
- LUFS: {analysis_data['lufs']}
- Avg Transient Strength: {analysis_data['avg_transient_strength']}
- Max Transient Strength: {analysis_data['max_transient_strength']}
- Transients: {analysis_data['transient_description']}
- Spectral balance note: {analysis_data['spectral_balance_description']}
- Dynamic range: {analysis_data['dynamic_range']}
- Stereo width: {analysis_data['stereo_width']}
- Bass profile: {analysis_data['bass_profile']} ({analysis_data['low_end_energy_ratio']})
  {analysis_data.get('low_end_description', '')}
- Band energies: {json.dumps(analysis_data['band_energies'], indent=2)}
{peak_warning}

### Reasoning Step
Before writing the bullet points, briefly reflect on what stands out from the analysis data.
Write 2–3 sentences summarizing key characteristics or concerns about the mix (this part will not be shown to the user).

### Bullet Point Feedback
Now return exactly 2–3 bullet points.

{format_rule.strip()}

⚠️ Do **not** include a title, greeting, summary, or closing line.

{example_output}
""".strip()


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
    user_question = re.sub(r"[^\w\s.,!?@&$()\-+=:;\'\"/]", "", user_question)  # scrub suspicious chars
    user_question = html.escape(user_question)[:300]  # escape HTML and truncate

    combined_prompt = f"""
You are a helpful and professional **audio engineer assistant**.

### Track Analysis
{analysis_text}

### Prior Feedback
{feedback_text}

### User's Follow-Up Question
"{user_question}"

### Instructions
- Use the analysis and feedback above as context.
- Answer the user's follow-up clearly and concisely.
- Do **not** repeat the full analysis or feedback.
- If the question is unclear, do your best to interpret it based on the feedback and analysis.

Respond below:
"""
    print("💬 Sending follow-up prompt:\n", combined_prompt)

    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": combined_prompt}]
    )
    return response.choices[0].message.content.strip()

