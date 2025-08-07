from openai import OpenAI
from app.utils import normalize_type, normalize_profile, normalize_genre, ALLOWED_GENRES, normalize_subgenre
import os
from dotenv import load_dotenv
load_dotenv()
import html
import re
from typing import List
from app.token_tracker import add_token_usage

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
        """
        You are a professional mixing engineer with deep expertise in {genre}, especially {subgenre}.  
        The user has uploaded a **final mixdown (pre-master)** for review.
        
        Your job is to assess the **technical quality** of this mix from a signal-level perspective.
        
        🎯 Focus areas:
        - Is there **sufficient headroom**? (Target LUFS around -16, peak around -1.0 dBFS)
        - Does the **dynamic range** feel natural and unclipped?
        - Are there any **frequency balance** concerns (especially in low-end)?
        - Is there **stereo clarity** without excessive width or phase issues?
        - Are the **transients** preserved?
        
        🚫 Do not recommend:
        - Loudness-enhancing tools (limiters, maximizers, compression chains)
        - Techniques used to finalize or release tracks
        
        Your feedback should be friendly and help the user **prepare** their mix for the next step, not enhance or master it.  
        Be clear, encouraging, and technically specific.
        
        End with a brief readiness summary:
        
        🟢 Technically ready  
        🟡 Needs minor tweaks  
        🔴 Major issues to fix
        """
    ),
    "mastering": (
        """
        You are a professional mastering engineer with deep expertise in {genre}, especially {subgenre}.  
        The user has uploaded a **final mixdown (pre-master)**, ready to be mastered.
        Use friendly language to:
        - Recommend mastering tools and techniques that would best enhance this track
        - Consider genre expectations when making your decisions
        
        Base your suggestions on signal-level and spectral data from the mix.  
        You do **not** have access to stems, only the final stereo file.
        
        Focus on mastering-specific adjustments such as:
        - **Loudness targeting (LUFS / RMS)** — How much gain or limiting is appropriate?
        - **Compression** — Would you apply broadband or multiband compression? If so, where and why?
        - **EQ decisions** — Any tonal imbalances to correct or enhance?
        - **Low-end mono folding** — Would you collapse the low end below 100Hz to mono? Why or why not?
        - **Stereo enhancement** — Would you apply width processing or leave it untouched?
        - **True peak limiting** — What ceiling would you use and why?
        - **Metering targets** — What values would you aim for post-master?
        
        Use mastering terminology and tools (e.g., linear-phase EQ, M/S processing, multiband comp, true peak limiter).  
        Explain *why* each recommendation would improve the master based on the data.
        
        Be genre-aware in your judgments. For example, heavy limiting might be fine in EDM, but not in jazz or folk.
        
        Do **not** comment on mix-specific elements like vocals, instrument balance, or arrangement.
        
        Conclude with a short summary of the suggested mastering chain and your rationale.
        """
    ),
    "master": (
        """
        You are a professional mastering engineer with deep expertise in {genre}, especially {subgenre}.  
        The user has uploaded a **finished, mastered track** for review.
        
        
        Your job is to evaluate whether the track meets **professional mastering standards** for its genre and identify any potential issues or improvements.  
        You are reviewing the final stereo master — you do **not** have access to stems or mix versions.
        
        Base your feedback on technical signal analysis (LUFS, RMS, dynamic range, stereo image, spectral balance, transient profile, peak level, etc.).
        
        Use friendly language to comment on the following areas::
        
        - **Loudness** — Is the LUFS/RMS competitive for the genre? Too loud or too soft?
        - **True Peak** — Are there clipping risks? Does the limiter ceiling follow best practices (e.g., -1.0 dBTP)?
        - **Dynamic Range** — Is it too crushed or too soft compared to what’s typical?
        - **Frequency Balance** — Is the tonal balance suitable for this genre?
        - **Low-end and Sub** — Controlled and tight, or muddy and overpowering?
        - **Stereo Width & Phase** — Wide enough without phase issues? Any mono compatibility concerns?
        - **Transients** — Are they crisp, punchy, or squashed?
        
        Be genre-aware in your judgments. For example, heavy limiting might be fine in EDM, but not in jazz or folk.
        
        Conclude with a summary judgment:
        
        🟢 Master sounds professional and release-ready  
        🟡 Acceptable, but some adjustments could improve quality  
        🔴 Needs revision — the master has issues that affect competitiveness or translation
        
        Use friendly, helpful language that guides the user toward high-quality results."""
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
- Start with "INSIGHT": Describe in plain but friendly language what feels off or unusual in the sound.
- Follow with "SUGGESTION": Suggest friendly a simple, actionable fix without technical terms.
- Use 1–2 short, friendly sentences.
- Briefly say why the suggestion might help, using intuitive, listener-friendly terms.
""",

    "detailed": """
Each bullet must:
- Begin with "INSIGHT": Describe friendly a clear mix/mastering issue using basic production terms.
- Follow with "SUGGESTION": Suggest an actionable tip (e.g., EQ, reverb, compression) with a short reason why.
- Use 2–3 clear sentences.
- Reference analysis data or genre norms when helpful.
""",

    "pro": """
Each bullet must:
- Start with "INSIGHT": Use technical but friendly language to precisely identify the issue.
- Follow with "SUGGESTION": Provide a targeted, technique-based recommendation (e.g., transient shaping, multiband sidechaining).
- Keep it sharp and focused: 2–3 dense, information-rich but friendly sentences.
- Justify the advice based on analysis or genre expectations.
"""
}

EXAMPLE_OUTPUTS = {
    "simple": '''
#### Example Output:
- INSIGHT: The overall loudness is lower than typical for this genre.
  SUGGESTION: Leave enough headroom for mastering, but aim for a slightly louder mixdown around -14 to -16 LUFS.

- INSIGHT: The low-end energy dominates the spectrum slightly.
  SUGGESTION: Consider reducing sub or bass levels or using gentle EQ to improve overall balance.
''',

    "detailed": '''
#### Example Output:
- INSIGHT: The RMS level is at -13.5 dB, which might be a bit high for a clean mixdown in {genre}.
  SUGGESTION: Lowering it to around -15 dB can preserve headroom and give mastering more flexibility.

- INSIGHT: There's a strong low-end focus with elevated energy below 100 Hz.
  SUGGESTION: Apply high-pass filtering on non-bass elements or use a dynamic EQ to manage low-frequency build-up.

- INSIGHT: The stereo image is slightly narrow in the upper frequency range.
  SUGGESTION: Use subtle stereo widening or mid/side EQ to enhance spaciousness without affecting mono compatibility.
''',

    "pro": '''
#### Example Output:
- INSIGHT: The dynamic range is high (16 dB), which is clean but may lack the energy typical of {subgenre}.
  SUGGESTION: Consider applying light compression or limiting to tighten the dynamic range slightly for more punch.

- INSIGHT: The transient peaks are sharp and could be perceived as aggressive in some playback systems.
  SUGGESTION: Use transient shaping or soft limiting to smooth the harshest peaks while maintaining impact.

- INSIGHT: The spectral balance leans heavily toward the low-mids, causing some muddiness.
  SUGGESTION: Use a gentle cut between 150–300 Hz to reduce masking and improve overall clarity in the mix.
'''
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
Now return 3-4 bullet points for adjustments in the most crucial areas.

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
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    # response = client.chat.completions.create(
    #     model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    #     messages=[{"role": "user", "content": prompt}]
    # )

    # Add this after response
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = prompt_tokens + completion_tokens
    add_token_usage(total_tokens, model_name="gpt-4o-mini")

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
    prompt = (
        "You are an expert audio mastering engineer.\n"
        "Compare the following tracks in terms of:\n"
        "- Sonic cohesion across all tracks\n"
        "- Technical differences (LUFS, stereo width, spectral balance, etc.)\n"
        "- Strengths, weaknesses, and stylistic consistency\n\n"
        "Each track includes both technical analysis and prior AI feedback.\n"
        "Prior feedback uses 'INSIGHT:' and 'SUGGESTION:' to indicate observations and recommendations.\n\n"
        "Give a detailed comparison summary and specific suggestions where appropriate.\n\n"
    )

    for idx, entry in enumerate(comparison_data, 1):
        prompt += f"🎵 Track {idx}: {entry['track_name']}\n"
        prompt += f"📊 Analysis Summary:\n{entry['analysis_summary'].strip()}\n"
        prompt += f"💬 Prior Feedback:\n{entry['chat_history'].strip()}\n\n"

    prompt += (
        "### Comparison Summary\n"
        "Write a cohesive summary of how the tracks compare. Highlight what works well, what needs attention, and whether they sound like they belong together in an album or playlist.\n"
        "Use bullet points or clear section headings like 'Strengths', 'Weaknesses', and 'Suggestions'."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an experienced audio mastering engineer evaluating track cohesion and quality."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )

    # Add this after response
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = prompt_tokens + completion_tokens
    add_token_usage(total_tokens, model_name="gpt-4o-mini")

    return response.choices[0].message.content.strip()