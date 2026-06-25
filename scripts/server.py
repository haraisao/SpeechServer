'''
Copyright 2025 Isao Hara, RT Corporation.

Licensed under the Apache License, Version 2.0 (the “License”);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an “AS IS” BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and
limitations under the License.

'''
import datetime
import os
import yaml

from flask import Flask, request
from flask import jsonify
from flask import Blueprint

from vosk_recog import VoskRecognizer
from voicevox_synth import Voicevox
from gemini import Gemini


PJ_TOP = os.path.abspath(os.path.dirname(__file__) + "/..")

def load_yaml(fname):
    """ load yaml file """
    config_=None
    try:
        with open(fname, "r", encoding="utf-8") as yml:
            config_=yaml.safe_load(yml)
    except Exception as e:
        print(e)
    return config_

#
# for Flask
DOCUMENT_ROOT=os.environ.get('DOCUMENT_ROOT', PJ_TOP+'/html/')
TEMPLATE_ROOT=DOCUMENT_ROOT
#print(DOCUMENT_ROOT, TEMPLATE_ROOT)

blueprint_app=Blueprint('html', __name__, static_url_path='', static_folder=DOCUMENT_ROOT)
app=Flask(__name__, template_folder=TEMPLATE_ROOT, static_folder=None)
app.register_blueprint(blueprint_app)
app.config['JSON_AS_ASCII'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

app.secret_key='SpeechServer_for_AI_Stackchan'
app.permanent_session_lifetime = datetime.timedelta(hours=16)

KEY_FILE=os.environ.get('KEY_FILE', PJ_TOP+'/conf/application_key.yaml' )
config=load_yaml(KEY_FILE)

voice_v = Voicevox(core_dir=os.path.join(PJ_TOP, "lib/voicevox_core"))
vosk = VoskRecognizer(model_path=os.path.join(PJ_TOP, "lib/vosk-model-ja-0.22"))

key=config['gemini_key']
gemini=Gemini(key)
gemini.set_prompt("あたなは、小さなスーパーロボット「スタックチャン」です。現在、東京にいます。対話の応答は、東京にいることを前提に、２０字以内で答えてください。")

#
#
# REST_API
@app.route('/vosk', methods=["POST"])
def rest_vosk():
    """ Request STT """
    response = vosk.request(request.data)
    print(response)
    return response

@app.route('/tts', methods=["POST"])
def rest_tts():
    """ Request TTS """
    response = voice_v.request(request.data)
    return jsonify(response)

@app.route('/talk_str', methods=["POST"])
def rest_talk_str():
    """ Request message to Gemini """
    txt=request.json['data']
    result_ = gemini.request(txt)
    response={'response': result_ }
    return jsonify(response)

@app.route('/talk', methods=["POST"])
def rest_talk():
    """ Talk to gemini """
    txt=request.json['data']
    result = gemini.request(txt)
    response = voice_v.synthesize(result)
    return jsonify(response)

@app.route('/chat', methods=["POST"])
def rest_chat():
    """  chat with Gemini by audio """
    txt = vosk.request(request.data)
    result = gemini.request(txt)
    response = voice_v.synthesize(result)
    return jsonify(response)

if __name__=='__main__':
    server_port = os.environ.get('PORT', '8000')
    app.run(debug=False, port=server_port, host='0.0.0.0')
