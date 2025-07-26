# AI Feedback Prompt Generation (`gpt_utils.py`)

This module contains key prompt templates, role definitions, communication style guides, and example outputs used to generate tailored AI feedback for the music mixing and mastering assistant. The main function assembles all parts dynamically into a detailed prompt sent to the AI model.

---

## Constants & Templates

### Reference Track Instruction

```python
REFERENCE_TRACK_INSTRUCTION = (
    "If a reference track analysis is provided, you MUST compare the submitted track's analysis with the reference track's data."
    "Give specific feedback on differences and how to improve the submitted track based on the comparison."
    "If no reference data is available, Do NOT mention, assume, or imply any reference track in the feedback."
)

Enforces that the AI only mentions a reference track when reference data is available.
Guides the AI to provide comparison-based feedback.


ROLE_CONTEXTS = {
    "mixdown": "You are a professional **mixing engineer reviewing a mixdown** with deep knowledge of {genre}, especially {subgenre}.",
    "mastering": "You are a professional **mastering engineer giving mastering advice** for this mixdown with deep knowledge of {genre}, especially {subgenre}.",
    "master": "You are a professional **mastering engineer reviewing a finished master** to assess its quality with deep knowledge of {genre}, especially {subgenre}.",
}

Defines the AI persona and task based on the feedback type.
Ensures contextual and role-specific feedback.


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

Adapts feedback tone and complexity to user-selected detail level.


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


Explanation:
Validates inputs against allowed roles, genres, and profiles.
Escapes HTML in genre and subgenre for safe prompt formatting.
Dynamically inserts audio analysis and optional reference track data.
Includes detailed instructions on tone, style, and bullet format.
Enforces no extraneous text in AI output to ensure clean feedback.