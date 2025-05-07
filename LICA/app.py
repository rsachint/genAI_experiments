from flask import Flask, request, jsonify
import base64, io, os, requests

app = Flask(__name__, static_folder='public', static_url_path='')
API_KEY = os.getenv('SARVAM_API_KEY')
STT_URL = 'https://api.sarvam.ai/speech-to-text'
STT_TURL = 'https://api.sarvam.ai/speech-to-text-translate'
TTS_URL = 'https://api.sarvam.ai/text-to-speech'

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    return app.send_static_file('index.html')

@app.route('/translate_play', methods=['POST'])
def translate_play():
    data = request.get_json(force=True)
    role = data.get('role')
    audio_b64 = data.get('audio')
    if role not in ('teacher','student') or not audio_b64:
        return jsonify({'error':'Missing role/audio'}),400
    audio_bytes = base64.b64decode(audio_b64)

    # STT
    files = {'file':('input.wav',io.BytesIO(audio_bytes),'audio/wav')}
    headers = {'API-Subscription-Key':API_KEY}
    stt = requests.post(STT_URL,headers=headers,files=files, data={'language_code':'hi-IN' if role=='teacher' else 'pa-IN'})
    stt.raise_for_status()
    transcript = stt.json().get('transcript','')

    # Translate via STT-TTT API
    files2={'file':('input.wav',io.BytesIO(audio_bytes),'audio/wav')}
    data2={'model':'saarikav2','target_language_code':'pa-IN' if role=='teacher' else 'hi-IN'}
    tr = requests.post(STT_TURL,headers=headers,files=files2,data=data2)
    tr.raise_for_status()
    translated = tr.json().get('transcript','')

    # TTS
    payload={'text':translated,'target_language_code':'pa-IN' if role=='teacher' else 'hi-IN','speaker':'anushka' if role=='teacher' else 'karun'}
    tts = requests.post(TTS_URL,headers={'Content-Type':'application/json','API-Subscription-Key':API_KEY},json=payload)
    tts.raise_for_status()
    audios=tts.json().get('audios',[])
    if not audios: return jsonify({'error':'No audio'}),500

    return jsonify({'original':transcript,'translated':translated,'audio':audios[0]})

if __name__=='__main__':
    port = int(os.getenv('PORT',8000))
    app.run(host='0.0.0.0',port=port)
