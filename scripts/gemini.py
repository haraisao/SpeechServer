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
import json
import requests

def load_conf(fname):
    """ Load configuration file"""
    with open(fname, "r", encoding='utf-8') as f:
        conts = f.read()
    keys=conts.split("\n")
    res={}
    for x in keys:
        try:
            k,v = x.split("=")
            res[k]=v
        except Exception as e:
            print(e)

    return res

def save_conf(fname, conf):
    """ Save configuration file """
    with open(fname, "w", encoding='utf-8') as file:
        for k in conf:
            file.write(f"{k}={conf[k]}\n")
    return

def get_file_contents(fname):
    """ load content from file """
    with open(fname, "r", encoding="utf-8") as f:
        conts = f.read()
    return conts

def load_json(fname):
    """ load Json file with comment """
    data_ = get_file_contents(fname)
    data = []
    for line in data_.split("\n"):
        pos = line.find("#")
        if pos >= 0:
            data.append(line[:pos])
        else:
            data.append(line)
    return json.loads("\n".join(data))

def save_json(fname, conf):
    """ Save json to file """
    with open(fname, "w", encoding='utf-8') as file:
        file.write(json.dumps(conf))
    return

class Gemini(object):
    """ Access gemini """
    def __init__(self, apikey):
        self._endpoint = "https://generativelanguage.googleapis.com/v1beta/interactions"
        self._apikey = apikey

        self.model =  "gemini-3.1-flash-lite"
        self._lang = 'ja-JP'
        self.prompt = ""

        self.conf = load_conf("gemini.txt")
        if "InteractionID" in self.conf:
            self.previous_interaction=self.conf.get("InteractionID")
        else:
            self.previous_interaction=""

        self.generation_config= {"thinking_level": "low"}
        self.functions = []
        self.mcp_funcall = None

    def reset_chat(self):
        """ clear interaction_id """
        self.previous_interaction=""
        return

    def set_prompt(self, prompt):
        """ set prompt """
        self.prompt=prompt
        return

    def set_interaction_id(self, txt=""):
        """ set interaction id """
        self.previous_interaction=txt

    def get_response_text(self, result):
        """ get response text """
        for res in result["steps"]:
            if res["type"] == "model_output":
                txt = ""
                for x in res["content"]:
                    if x["type"] == "text":
                        txt += x["text"]
                return result["id"], txt
        return None

    def get_response_func(self, result):
        """ get mcp fnction call """
        try:
            for res in result["steps"]:
                if res["type"] == "function_call":
                    return result["id"],res
            return None
        except AttributeError as e:
            print(result, e)

    def load_mcp_func(self, fname):
        """ load mcp definition from file """
        func=load_json(fname)
        if func:
            self.functions.append(func)

    def save_interacation_id(self, fname="gemini.txt"):
        """ save current interaction id to file """
        self.conf["InteractionID"] = self.previous_interaction
        save_conf(fname, self.conf)

    def load_interacation_id(self, fname="gemini.txt"):
        """ load interaction id from file """
        conf = load_conf(fname)
        if conf.get("InteractionID"):
            self.previous_interaction=conf.get("InteractionID")

    def request_gemini(self, text, save_id=True, timeout=10):
        """ Request to gemini """
        url = self._endpoint + "?key=" + self._apikey
        headers = { 'Api-Revision': '2026-05-20',
                    'Content-Type' : 'application/json' }
        data = {
            "model": self.model,
            "input": text,
        }

        if self.generation_config:
            data["generation_config"] = self.generation_config

        if self.previous_interaction:
            data["previous_interaction_id"] = self.previous_interaction

        if self.prompt:
            data["system_instruction"] =  self.prompt

        data["tools"] = [
                {"type": "google_search" }
                ]
        for fn in self.functions:
            data["tools"].append(fn)

        try:
            req_data = json.dumps(data).encode('utf-8')
            result = requests.post(url, data=req_data, headers=headers, timeout=timeout)
            response = result.json()
            if 'id' in response:
                self.previous_interaction = response['id']
                if save_id:
                    self.conf["InteractionID"] = response['id']
                    save_conf("gemini.txt", self.conf)
            return response
        except Exception as e:
            print(result.json())
            print ('Error', e)
            return ""

    def response_mcp(self, interaction, funcall, result, timeout=10):
        """ response mcp result """
        url = self._endpoint + "?key=" + self._apikey
        headers = { 'Api-Revision': '2026-05-20',
                    'Content-Type' : 'application/json' }

        data = {
            "model": self.model,
            "input": [{
                "type": "function_result",
                "name": funcall["name"],
                "call_id": funcall["id"],
                "result": [ {"type": "text", "text": json.dumps(result)}]
              }
            ],
            "previous_interaction_id": interaction
        }

        try:
            req_data=json.dumps(data).encode('utf-8')
            result = requests.post(url, data=req_data, headers=headers, timeout=timeout)
            response = result.json()
            if 'id' in response:
                self.previous_interaction = response['id']
                self.conf["InteractionID"] = response['id']
                save_conf("gemini.txt", self.conf)
            return response
        except Exception as e:
            print(result.json())
            print ('Error', e)
            return ""

    def talk(self, data):
        """ talk to gemini """
        response=self.request_gemini(data)
        if response:
            return response
        return None

    def mcp_response(self, result):
        """ response MCP """
        if self.mcp_funcall:
            interaction = self.mcp_funcall[0]
            funcall = self.mcp_funcall[1]
            res=self.response_mcp(interaction, funcall, result)
            _ = self.get_response_text(res)
            self.mcp_funcall = None

    def request(self, txt):
        """ Requst to gemini """
        result = self.request_gemini(txt)
        mcp_funcall = self.get_response_func(result)
        if mcp_funcall:
            self.mcp_funcall = mcp_funcall
            self.mcp_response({"result": "Finished"})
            return
        response_text = self.get_response_text(result)
        print(response_text[1])
