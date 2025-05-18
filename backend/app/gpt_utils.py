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

def generate_feedback_prompt(genre: str, analysis_data: dict) -> str:
    return f"""
    You are a professional mixing and mastering engineer with deep knowledge of {genre} music.

    Here is an audio track's analysis:
    - Peak: {analysis_data['peak_db']} dB
    - RMS: {analysis_data['rms_db']} dB
    - LUFS: {analysis_data['lufs']}
    - Dynamic range: {analysis_data['dynamic_range']}
    - Stereo width: {analysis_data['stereo_width']}
    - Key: {analysis_data['key']}
    - Tempo: {analysis_data['tempo']} BPM
    - Bass profile: {analysis_data['bass_profile']}
    - Band energies: {json.dumps(analysis_data['band_energies'], indent=2)}

    🎯 Your task:
    Return **exactly 2–3 bullet points**, each one should:
    - Name 1 issue clearly
    - Give a **concrete, genre-relevant** improvement tip
    - Keep each bullet max 2–3 sentences

    🎵 Only return the list of bullet points.
    """
# Please respond with a list of issues and improvement tips.
# def generate_feedback_response(prompt: str) -> str:
#     response = openai.ChatCompletion.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return response.choices[0].message["content"]

'''FAKE RESPONSE FOR TESTING'''
# def generate_feedback_response(prompt: str) -> str:
#     print("Mock prompt sent to GPT:\n", prompt)  # For debugging
#     return """\
# Sure! Here are 2–3 mixing suggestions based on your track:
#
# - The bass profile is slightly heavy. Consider using a high-pass filter to clean sub-bass rumble.
# - The stereo width is 'wide'. Check for mono compatibility.
# - LUFS is within range, but a slight gain staging tweak may help with headroom.
# """
def generate_feedback_response(prompt: str) -> str:
    print("🔍 Prompt being sent to GPT:\n", prompt)
    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
