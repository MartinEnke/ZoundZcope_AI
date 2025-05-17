import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_feedback(analysis_data):
    prompt = f"""
    You're an expert audio mastering engineer.
    Here's the track analysis:
    - Peak: {analysis_data['peak_db']} dB
    - RMS: {analysis_data['rms_db']} dB
    - LUFS: {analysis_data['lufs']}
    - Dynamic range: {analysis_data['dynamic_range']}
    - Stereo width: {analysis_data['stereo_width']}
    - Key: {analysis_data['key']}
    - Tempo: {analysis_data['tempo']} BPM
    - Low-end energy: {analysis_data['low_end_energy']}
    - Issues: {', '.join(analysis_data['issues'])}

    Please, give me mixing and mastering advice based on these stats.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]