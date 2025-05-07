import os
import io
import base64
import threading
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from pydub import AudioSegment
from pydub.playback import play
import requests

load_dotenv()
API_KEY = os.getenv("SARVAM_API_KEY")
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate_play', methods=['POST'])
def translate_and_play():
    data = request.get_json()
    role = data.get('role')  # 'teacher' or 'student'
    audio_b64 = data.get('audio')

    if not API_KEY or not audio_b64 or not role:
        return jsonify({'error': 'Missing data'}), 400

    # Step 1: Save audio
    audio_data = base64.b64decode(audio_b64.split(',')[1])
    tmp_path = f"/tmp/{role}_input.wav"
    with open(tmp_path, "wb") as f:
        f.write(audio_data)

    # Step 2: STT
    stt = requests.post(
        "https://api.sarvam.ai/speech-to-text",
        headers={"API-Subscription-Key": API_KEY},
        files={"file": ("audio.wav", open(tmp_path, "rb"), "audio/wav")},
        data={"model": "saarika:v2", "language_code": "unknown"}
    ).json()
    transcript = stt.get("transcript", "")
    detected_lang = stt.get("language_code", "hi-IN")

    # Step 3: Translate
    src = "hi-IN" if role == "teacher" else "pa-IN"
    tgt = "pa-IN" if role == "teacher" else "hi-IN"
    translation = requests.post(
        "https://api.sarvam.ai/translate",
        headers={"API-Subscription-Key": API_KEY, "Content-Type": "application/json"},
        json={"input": transcript, "source_language_code": src, "target_language_code": tgt, "mode": "formal"}
    ).json().get("translated_text", "")

    # Step 4: TTS
    speaker = "anushka" if role == "teacher" else "karun"
    tts = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        headers={"API-Subscription-Key": API_KEY, "Content-Type": "application/json"},
        json={
            "text": translation, "target_language_code": tgt, "speaker": speaker,
            "pitch": 0.0, "pace": 1.0, "loudness": 1.0, "speech_sample_rate": 22050
        }
    ).json()
    raw_audio = base64.b64decode(tts.get("audios", [""])[0])
    audio_segment = AudioSegment.from_file(io.BytesIO(raw_audio), format="wav")
    threading.Thread(target=play, args=(audio_segment,), daemon=True).start()

    return jsonify({
        "original": transcript,
        "translated": translation,
        "lang": detected_lang
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
