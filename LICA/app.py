from flask import Flask, render_template, request, jsonify
import os
import base64
import requests
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
API_KEY = os.getenv("SARVAM_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate_play', methods=['POST'])
def translate_and_play():
    data = request.get_json()
    role = data.get('role')
    audio_b64 = data.get('audio')

    if not API_KEY or not audio_b64 or not role:
        return jsonify({'error': 'Missing data'}), 400

    # Save audio to temp file
    audio_data = base64.b64decode(audio_b64.split(',')[1])
    tmp_path = f"/tmp/{role}_input.wav"
    with open(tmp_path, "wb") as f:
        f.write(audio_data)

    # Step 1: STT (Sarvam API)
    stt_response = requests.post(
        "https://api.sarvam.ai/speech-to-text",
        headers={"API-Subscription-Key": API_KEY},
        files={"file": ("audio.wav", open(tmp_path, "rb"), "audio/wav")},
        data={"model": "saarika:v2", "language_code": "unknown"}
    ).json()

    transcript = stt_response.get("transcript", "")

    # Step 2: Define language direction
    if role == "teacher":
        src, tgt, speaker, target_box = "hi-IN", "pa-IN", "anushka", "student"
    else:
        src, tgt, speaker, target_box = "pa-IN", "hi-IN", "karun", "teacher"

    # Step 3: Translate (Sarvam)
    translation = requests.post(
        "https://api.sarvam.ai/translate",
        headers={"API-Subscription-Key": API_KEY, "Content-Type": "application/json"},
        json={
            "input": transcript,
            "source_language_code": src,
            "target_language_code": tgt,
            "mode": "formal"
        }
    ).json().get("translated_text", "")

    # Step 4: TTS (Sarvam)
    tts_response = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        headers={"API-Subscription-Key": API_KEY, "Content-Type": "application/json"},
        json={
            "text": translation,
            "target_language_code": tgt,
            "speaker": speaker
        }
    ).json()

    audio_out_b64 = tts_response.get("audios", [""])[0]

    return jsonify({
        "original": transcript,
        "translated": translation,
        "audio": audio_out_b64,
        "target_box": target_box
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

