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
import binascii
import json
import traceback
from flask import jsonify
import vosk

class VoskRecognizer:
    """ VOSK adaptor """
    def __init__(self, model_path="vosk-model-ja-0.22", sample_rate=16000):
        self.model=vosk.Model(model_path)
        self.sample_rate=sample_rate
        self.recognizer=vosk.KaldiRecognizer(self.model, sample_rate)

    def execute(self, data):
        """ execute STT """
        self.recognizer.AcceptWaveform(data)
        return self.recognizer.Result()

    def request(self, data):
        """ Request from client """
        try:
            param=json.loads(data)
            data_ = param['data']
        except:
            data_=data
        try:
            bdata = binascii.a2b_base64(data_)
            res=self.execute(bdata)
            response=json.loads(res)
            recog_txt=response['text'].replace(' ', '')
            if data == data_ :
                return recog_txt
            else:
                return jsonify({'result': recog_txt })
        except Exception as e:
            traceback.print_exc()
            return False


