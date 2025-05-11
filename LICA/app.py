from flask import Flask, request, jsonify
import os, base64, io, requests, logging
from dotenv import load_dotenv

# Initialize Flask app to serve static files from 'templates'
app = Flask(__name__, static_folder='templates', static_url_path='')

# Send DEBUG logs to stdout
logging.basicConfig(level=logging.DEBUG)
# Flask’s own logger
app.logger.setLevel(logging.DEBUG)
# Gunicorn’s logger (if you need it)
if 'gunicorn.error' in logging.root.manager.loggerDict:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    gunicorn_logger.setLevel(logging.DEBUG)
# ————————————————————————


load_dotenv()
API_KEY = os.getenv("SARVAM_API_KEY")

# Sarvam API endpoints
STT_URL = 'https://api.sarvam.ai/speech-to-text'
TRANSLATE_URL = 'https://api.sarvam.ai/translate'
TTS_URL = 'https://api.sarvam.ai/text-to-speech'

# Serve frontend static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    return app.send_static_file('index.html')

# Unified translate and play endpoint
@app.route('/translate_play', methods=['POST'])
def translate_play():
    app.logger.debug("Incoming /translate_play request: %s", request.get_json())
    data = request.get_json(force=True)
    role = data.get('role')
    audio_b64 = data.get('audio')

    # Validate input
    if not API_KEY or role not in ('teacher', 'student') or not audio_b64:
        return jsonify({'error': 'Missing or invalid role/audio'}), 400

    # Decode audio from Base64
    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as e:
        return jsonify({'error': 'Invalid Base64 audio', 'detail': str(e)}), 400

    app.logger.debug("Decoded audio bytes: %d bytes", len(audio_bytes))
    
    # 1) Speech-to-Text (STT)
    stt_files = {'file': ('input.wav', io.BytesIO(audio_bytes), 'audio/wav')}
    stt_headers = {
        'API-Subscription-Key': API_KEY,
        'Accept': 'application/json'
    }
    stt_data = {
        'model': 'saarika:v2',
        'language_code': 'hi-IN' if role == 'teacher' else 'pa-IN'
    }
    stt_resp = requests.post(STT_URL, headers=stt_headers, files=stt_files, data=stt_data)
    if not stt_resp.ok:
        return jsonify({'error': 'STT failed', 'detail': stt_resp.text}), 502
    transcript = stt_resp.json().get('transcript', '')
    app.logger.debug("STT response [%s]: %s", stt_resp.status_code, stt_resp.text)
    
    # 2) Text Translate
    translate_headers = {
        'API-Subscription-Key': API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    translate_payload = {
        'model': 'mayura:v1',
        'input': transcript,
        'source_language_code': 'hi-IN' if role == 'teacher' else 'pa-IN',
        'target_language_code': 'pa-IN' if role == 'teacher' else 'hi-IN',
        'text': transcript
    }
    translate_resp = requests.post(TRANSLATE_URL, headers=translate_headers, json=translate_payload)
    if not translate_resp.ok:
        return jsonify({'error': 'Translate failed', 'detail': translate_resp.text}), 502
    translated_text = translate_resp.json().get('translated_text', '')

    app.logger.debug("Translate response [%s]: %s, %s, %s", translate_resp.status_code, translate_resp.text, translated_text, translate_resp.json())
    
    # 3) Text-to-Speech (TTS)
    tts_headers = {
        'API-Subscription-Key': API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    tts_payload = {
        'model': 'bulbul:v2',
        'text': translated_text,
        'target_language_code': 'pa-IN' if role == 'teacher' else 'hi-IN',
        'speaker': 'anushka' if role == 'teacher' else 'karun',
        'speech_sample_rate': 22050
    }
    tts_resp = requests.post(TTS_URL, headers=tts_headers, json=tts_payload)
    if not tts_resp.ok:
        return jsonify({'error': 'TTS failed', 'detail': tts_resp.text}), 502
    audio_b64_list = tts_resp.json().get('audios', [])
    if not audio_b64_list:
        return jsonify({'error': 'No audio returned'}), 500
    audio_out_b64 = audio_b64_list[0]

    app.logger.debug("TTS response [%s]: %s", tts_resp.status_code, tts_resp.text)

    # Return combined response
    return jsonify({
        'original': transcript,
        'translated': translated_text,
        'audio': audio_out_b64
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
