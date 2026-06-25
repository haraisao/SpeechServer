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
import os
import traceback
import json
import base64

from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
import soundfile as sf
import resampy


VOICEVOX_CORE = os.path.join(os.path.dirname(__file__), "voicevox_core")
#
#
def setup_voicevox(core_dir=VOICEVOX_CORE, model="0.vvm"):
    """ Setup Voicevox """
    voicevox_onnxruntime_path = os.path.join(core_dir,
				                            "onnxruntime/lib/",
				                            Onnxruntime.LIB_VERSIONED_FILENAME)
    open_jtalk_dict_dir = os.path.join(core_dir,
				                        "dict/open_jtalk_dic_utf_8-1.11")
    synthesizer = Synthesizer(Onnxruntime.load_once(
	 	                        filename=voicevox_onnxruntime_path),
		                        OpenJtalk(open_jtalk_dict_dir))

    model_ = os.path.join(core_dir, "models/vvms", model)
    with VoiceModelFile.open(model_) as model:
        synthesizer.load_voice_model(model)
    return synthesizer

def save_audio(fname, data):
    """ Save audio to file """
    with open(fname, "wb") as file:
        file.write(data)

def load_audio(fname):
    """ load audio from file """
    with open(fname, "rb") as file:
        data = file.read()
    return data

def get_tts_sentence(txt):
    """ get TTS sentence """
    res=[]
    prev = 0
    for i in range(len(txt)):
        if txt[i] in ["。", "?", "!", "？", "！"]:
            res.append(txt[prev:(i+1)].strip())
            prev = i+1
    if txt[prev:].strip():
        res.append(txt[prev:].strip())
    return res

#
#
class Voicevox:
    """ Voicevox adaptor """
    def __init__(self, name="voicevox", core_dir=None):
        #
        # Parameters
        if core_dir is None:
            self.core_dir = VOICEVOX_CORE
        else:
            self.core_dir = core_dir
        self.model_file = "0.vvm"
        self.synthesizer = setup_voicevox(self.core_dir, self.model_file)

        self.style_id = 2

    def synthesize(self, txt, s_id=2):
        """ convert text to audio """
        try:
            self.style_id = s_id
            wav = self.synthesizer.tts(txt, self.style_id)
            fname='synth.wav'
            save_audio(fname, wav)
            x, fs = sf.read(fname)
            y = resampy.resample(x, sr_orig=fs, sr_new=8000)
            sf.write(fname, data=y, samplerate=8000)
            wav2 = load_audio(fname)
            res={'audio': base64.b64encode(wav2).decode()}
            return res
        except Exception as e:
            traceback.print_exc()
        return

    def request(self, data):
        """ Request from client """
        print("request:", data)
        param=json.loads(data)
        try:
            speaker_id = param['speaker']
        except KeyError as e:
            print("Key error", e)
            speaker_id=2
        result=self.synthesize(param['data'], speaker_id)
        return result
