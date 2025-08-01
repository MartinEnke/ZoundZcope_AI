from openai import OpenAI
from app.utils import normalize_type, normalize_profile, normalize_genre, ALLOWED_GENRES, normalize_subgenre
import os
from dotenv import load_dotenv
load_dotenv()
import html
import re
from typing import List


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# client = OpenAI(
#     base_url="https://api.together.xyz/v1",  # You can still use Together
# )


REFERENCE_TRACK_INSTRUCTION = (
    "If a reference track analysis is provided, you MUST compare the submitted track's analysis with the reference track's data."
    "Give specific feedback on differences and how to improve the submitted track based on the comparison."
    "If no reference data is available, Do NOT mention, assume, or imply any reference track in the feedback."
)

ROLE_CONTEXTS = {
    "mixdown": (
        "You are a professional mixing engineer with extensive expertise in {genre}, "
        "particularly {subgenre}. Your task is to review a mixdown or rough mix—not a mastered track. "
        "Focus on aspects relevant to mixdowns, especially noting that this is not a final master, "
        "so pay attention to levels such as RMS which differ from mastering."
    ),
    "mastering": (
        "You are a professional mastering engineer with deep knowledge of {genre}, especially {subgenre}. "
        "You provide mastering advice specifically for this mixdown, including recommendations on which tools "
        "and techniques to use to achieve mastering-quality audio metrics and standards."
    ),
    "master": (
        "You are a professional mastering engineer reviewing a finished master track. "
        "Your role is to assess the quality of the final master with specialized knowledge of {genre}, particularly {subgenre}."
    ),
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

FORMAT_RULES = {
    "simple": """
Each bullet must:
- Start with "ISSUE": Describe in plain but friendly language what feels off or unusual in the sound.
- Follow with "IMPROVEMENT": Suggest friendly a simple, actionable fix without technical terms.
- Use 1–2 short, friendly sentences.
- Briefly say why the suggestion might help, using intuitive, listener-friendly terms.
""",

    "detailed": """
Each bullet must:
- Begin with "ISSUE": Describe friendly a clear mix/mastering issue using basic production terms.
- Follow with "IMPROVEMENT": Suggest an actionable tip (e.g., EQ, reverb, compression) with a short reason why.
- Use 2–3 clear sentences.
- Reference analysis data or genre norms when helpful.
""",

    "pro": """
Each bullet must:
- Start with "ISSUE": Use technical but friendly language to precisely identify the issue.
- Follow with "IMPROVEMENT": Provide a targeted, technique-based recommendation (e.g., transient shaping, multiband sidechaining).
- Keep it sharp and focused: 2–3 dense, information-rich but friendly sentences.
- Justify the advice based on analysis or genre expectations.
"""
}

EXAMPLE_OUTPUTS = {
    "simple": """
#### Example Output:
- ISSUE: Compared to the reference track the bass is too loud and makes the track feel heavy.
  IMPROVEMENT: Turn the bass down a little and check how it sounds with vocals. 
  This will help make everything clearer.

- ISSUE: The sound is too crowded.
  IMPROVEMENT: Try making some sounds quieter or move them left and right. 
  This can make the track feel more open.
""",

    "detailed": """
#### Example Output:
- ISSUE: Compared to the reference track the RMS Level doesn't match the standard for a mixdown of this {genre}.  
  IMPROVEMENT: Aim for around -15 dB RMS to preserve headroom for mastering. 
  This helps the final master stay loud and punchy, especially in {subgenre}.
  
- ISSUE: The kick and bass are clashing in the low end.
  IMPROVEMENT: Use EQ to reduce overlapping frequencies and sidechain the bass to the kick. 
  This adds clarity to your low end.

- ISSUE: The vocals feel buried in the mix.
  IMPROVEMENT: Add light compression and EQ boost around 2-4 kHz to bring them forward without sounding harsh.
""",

    "pro": """
#### Example Output:
- ISSUE: Compared to the reference track, your low-end feels less controlled and slightly muddy.
  IMPROVEMENT: Try applying a dynamic EQ to tighten the sub frequencies, similar to the clean bass in the reference track.
  
- ISSUE: Excessive buildup around 100Hz is causing low-end smearing.
  IMPROVEMENT: Use a dynamic EQ or sidechain-triggered low-shelf cut on the bass. 
  This maintains punch while improving definition.

- ISSUE: The stereo image collapses in the high-mids.
  IMPROVEMENT: Use mid-side EQ or widening tools (e.g. MicroShift) to open up the 2–6 kHz range. 
  Essential for clarity in {subgenre} arrangements.
"""
}


def generate_feedback_prompt(genre: str, subgenre: str, type: str, analysis_data: dict, feedback_profile: str, ref_analysis_data: dict = None) -> str:
    """
            Constructs a detailed AI prompt combining role context, communication style,
            audio analysis data, reference track data (optional), and formatting instructions.

            Parameters:
                genre (str): Music genre, normalized.
                subgenre (str): Music subgenre, normalized.
                type (str): Feedback type ('mixdown', 'mastering', 'master').
                analysis_data (dict): Audio analysis metrics of the submitted track.
                feedback_profile (str): Desired feedback complexity ('simple', 'detailed', 'pro').
                ref_analysis_data (dict, optional): Reference track analysis for comparison.

            Returns:
                str: Formatted prompt string ready to be sent to the AI model.
            """

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

    context = (
            REFERENCE_TRACK_INSTRUCTION + "\n\n" + ROLE_CONTEXTS[type].format(
        genre=html.escape(genre),
        subgenre=html.escape(subgenre)
    )
    )
    communication_style = PROFILE_GUIDANCE[feedback_profile]

    # Add reference track data section if available
    ref_section = ""
    if ref_analysis_data:
        ref_section = f"""
    ### Reference Track Analysis (for comparison)
    - Peak: {ref_analysis_data['peak_db']} dB
    - RMS Peak: {ref_analysis_data['rms_db_peak']} dB
    - LUFS: {ref_analysis_data['lufs']}
    - Transients: {ref_analysis_data['transient_description']}
    - Spectral balance note: {ref_analysis_data['spectral_balance_description']}
    - Dynamic range: {ref_analysis_data['dynamic_range']}
    - Stereo width: {ref_analysis_data['stereo_width']}
    - Bass profile: {ref_analysis_data.get('low_end_description', '')}
    """

    peak_warning = ""
    if analysis_data.get("peak_issue_explanation"):
        peak_warning = f"\n⚠️ Peak warning: {analysis_data['peak_issue_explanation']}\n"

    format_rule = FORMAT_RULES.get(feedback_profile, FORMAT_RULES["detailed"])

    example_output = EXAMPLE_OUTPUTS.get(feedback_profile, "")

    # Final assembly
    return f"""
### Context
{context}

- **Respect the genre context**. F.e. only suggest reducing bass if clearly excessive relative to the genre’s typical sound.

### Communication Style
{communication_style}

### Track Analysis Data
- Peak: {analysis_data['peak_db']} dB
- RMS Peak: {analysis_data['rms_db_peak']} dB
- LUFS: {analysis_data['lufs']}
- Avg Transient Strength: {analysis_data['avg_transient_strength']}
- Max Transient Strength: {analysis_data['max_transient_strength']}
- Transients: {analysis_data['transient_description']}
If low-end is flagged as strong but typical for the genre, do NOT treat it as a problem unless masking, muddiness, or translation concerns are clearly implied.
- Spectral balance note: {analysis_data['spectral_balance_description']}
- Dynamic range: {analysis_data['dynamic_range']}
- Stereo width: {analysis_data['stereo_width']}
- Bass profile: {analysis_data.get('low_end_description', '')}
  (Genre: {genre} — please consider if the low-end level suits this genre’s typical sound.)

### REFERENCE TRACK
Here is analysis data for the reference track. Use this data to inform your feedback and compare where appropriate.
{ref_section}

{peak_warning}

### Reasoning Step
Use the reference track when provided as a benchmark to guide specific suggestions even when not typical for genre etc..
Before writing the bullet points, briefly reflect on what stands out from the analysis data.
Write 2–3 sentences summarizing key characteristics or concerns about the mix (this part will not be shown to the user).

### Bullet Point Feedback
Now return exactly 2–3 bullet points.

{format_rule.strip()}

⚠️ Do **not** include a title, greeting, summary, or closing line.

{example_output}
""".strip()


def generate_feedback_response(prompt: str) -> str:
    """
        Sends a prompt string to the AI model and returns the generated feedback text.

        Parameters:
            prompt (str): The fully constructed prompt containing context, instructions, and analysis data.

        Returns:
            str: The AI-generated feedback text, stripped of leading/trailing whitespace.
        """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    # response = client.chat.completions.create(
    #     model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    return response.choices[0].message.content.strip()


def generate_followup_response(analysis_text: str, feedback_text: str, user_question: str, thread_summary: str = "") -> str:
    """
        Builds a follow-up prompt incorporating prior analysis, feedback, user question,
        and optionally a summary of the follow-up conversation thread, then sends it to the AI.

        Parameters:
            analysis_text (str): Text description of the audio analysis.
            feedback_text (str): Previous AI feedback given to the user.
            user_question (str): The user's follow-up question.
            thread_summary (str, optional): Summary of previous follow-up messages for context.

        Returns:
            str: AI-generated answer to the follow-up question.
        """
    prompt = build_followup_prompt(analysis_text, feedback_text, user_question, thread_summary)
    return generate_feedback_response(prompt)


def build_followup_prompt(
    analysis_text: str,
    feedback_text: str,
    user_question: str,
    thread_summary: str = "",
    ref_analysis_data: dict = None,   # NEW parameter
) -> str:
    """
        Constructs a detailed prompt for AI follow-up feedback based on prior analysis,
        previous feedback, the user’s follow-up question, optional conversation summary,
        and optionally reference track analysis data.

        Parameters:
            analysis_text (str): Text description of the audio analysis.
            feedback_text (str): Previous AI feedback text.
            user_question (str): User’s follow-up question.
            thread_summary (str, optional): Summary of prior follow-up conversation for context.
            ref_analysis_data (dict, optional): Reference track analysis for comparison.

        Returns:
            str: A formatted prompt string ready for submission to the AI model.
        """

    # Clean and escape user question
    user_question = re.sub(r"[^\w\s.,!?@&$()\-+=:;\'\"/]", "", user_question.strip())[:400]
    user_question = html.escape(user_question)

    ref_section = ""
    if ref_analysis_data and isinstance(ref_analysis_data, dict):
        ref_section = f"""
        ### Reference Track Analysis (for comparison)
        - Peak: {ref_analysis_data.get('peak_db', 'N/A')} dB
        - RMS Peak: {ref_analysis_data.get('rms_db_peak', 'N/A')} dB
        - LUFS: {ref_analysis_data.get('lufs', 'N/A')}
        - Transients: {ref_analysis_data.get('transient_description', 'N/A')}
        - Spectral balance note: {ref_analysis_data.get('spectral_balance_description', 'N/A')}
        - Dynamic range: {ref_analysis_data.get('dynamic_range', 'N/A')}
        - Stereo width: {ref_analysis_data.get('stereo_width', 'N/A')}
        - Bass profile: {ref_analysis_data.get('low_end_description', '')}
        """
    else:
        print("Warning: ref_analysis_data missing or invalid:", ref_analysis_data)

    return f"""
You are a helpful and professional **audio engineer assistant**.

{"### Summary of Previous Conversation\n" + thread_summary + "\n" if thread_summary else ""}

### Track Analysis
{analysis_text}

{ref_section}

### Prior Feedback
{feedback_text}

### User's Follow-Up Question
"{user_question}"

### Instructions
- Use the analysis, feedback, and summary above as context.
- Do **not** repeat the full analysis or feedback.
- Answer the follow-up clearly and concisely.
- Stay on topic and be technically helpful.
- If the question is vague, use the existing context to infer intent.

Respond below:
"""


def generate_comparison_feedback(comparison_data: List[dict]) -> str:
    """
    Builds a multi-track comparison prompt and returns AI feedback.
    Each dict in `comparison_data` should contain:
        - 'track_name'
        - 'analysis_summary'
        - 'chat_history'

    Returns:
        str: AI-generated comparison feedback.
    """
    prompt = """You are an audio mastering engineer. 
    Compare the following tracks in terms of sonic cohesion, technical quality, 
    and stylistic consistency. Mention any differences, similarities, and possible 
    improvements relative to each other. If they seem identical, point that out as well.\n\n"""
    for idx, entry in enumerate(comparison_data, 1):
        prompt += f"🎵 Track {idx}: **{entry['track_name']}**\n"
        prompt += f"{entry['analysis_summary']}\n"
        prompt += f"🗨️ Chat Summary:\n{entry['chat_history']}\n\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an audio mastering engineer helping evaluate sonic cohesion."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
