from flask import Flask, request, jsonify
import os, base64, io, requests
from dotenv import load_dotenv

# Serve static files from templates
app = Flask(__name__, static_folder='templates', static_url_path='')
load_dotenv()
API_KEY = os.getenv("SARVAM_API_KEY")
STT_URL = 'https://api.sarvam.ai/speech-to-text'
STT_TURL = 'https://api.sarvam.ai/speech-to-text-translate'
TTS_URL = 'https://api.sarvam.ai/text-to-speech'

# Serve frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    return app.send_static_file('index.html')

@app.route('/translate_play', methods=['POST'])
def translate_play():
    data = request.get_json(force=True)
    role = data.get('role')
    audio_b64 = data.get('audio')

    if not API_KEY or role not in ('teacher','student') or not audio_b64:
        return jsonify({'error': 'Missing or invalid data'}), 400

    # Decode Base64 audio blob
    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as e:
        return jsonify({'error': 'Invalid base64 audio', 'detail': str(e)}), 400

    # STT
    stt_files = {'file': ('input.wav', io.BytesIO(audio_bytes), 'audio/wav')}
    stt_headers = {'API-Subscription-Key': API_KEY}
    stt_data = {'model': 'saarikav2', 'language_code': 'hi-IN' if role=='teacher' else 'pa-IN'}
    stt_resp = requests.post(STT_URL, headers=stt_headers, files=stt_files, data=stt_data)
    stt_resp.raise_for_status()
    transcript = stt_resp.json().get('transcript', '')

    # Translate
    src, tgt = ('hi-IN','pa-IN') if role=='teacher' else ('pa-IN','hi-IN')
    tr_files = {'file': ('input.wav', io.BytesIO(audio_bytes), 'audio/wav')}
    tr_headers = {'API-Subscription-Key': API_KEY}
    tr_data = {'model': 'saarikav2', 'target_language_code': tgt}
    tr_resp = requests.post(STT_TURL, headers=tr_headers, files=tr_files, data=tr_data)
    tr_resp.raise_for_status()
    translated = tr_resp.json().get('transcript', '')

    # TTS
    tts_payload = {'text': translated, 'target_language_code': tgt, 'speaker': 'anushka' if role=='teacher' else 'karun'}
    tts_headers = {'API-Subscription-Key': API_KEY, 'Content-Type': 'application/json'}
    tts_resp = requests.post(TTS_URL, headers=tts_headers, json=tts_payload)
    tts_resp.raise_for_status()
    audios = tts_resp.json().get('audios', [])
    if not audios:
        return jsonify({'error': 'No audio returned'}), 500

    return jsonify({'original': transcript, 'translated': translated, 'audio': audios[0]})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
