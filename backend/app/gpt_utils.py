import openai
import os
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_feedback_prompt(genre: str, analysis_data: dict) -> str:
    return f"""
You're a professional mixing and mastering engineer with deep knowledge of {genre} music.
Here's the analysis of a {type} of my track. Please give 2–3 concise suggestions on what could be improved,
based on the genre’s standards and common practices.

Analysis:
- Peak: {analysis_data['peak_db']} dB
- RMS: {analysis_data['rms_db']} dB
- LUFS: {analysis_data['lufs']}
- Dynamic range: {analysis_data['dynamic_range']}
- Stereo width: {analysis_data['stereo_width']}
- Key: {analysis_data['key']}
- Tempo: {analysis_data['tempo']} BPM
- Bass profile: {analysis_data['bass_profile']}
- Band energies: {json.dumps(analysis_data['band_energies'], indent=2)}

Please respond with a list of issues and improvement tips.
"""

def generate_feedback_response(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

