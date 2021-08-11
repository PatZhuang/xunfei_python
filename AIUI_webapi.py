#-*- coding: utf-8 -*-

from QISR import SAMPLE_RATE_16K
import requests
import time
import hashlib
import base64
from requests.api import head
from rich import print
import json
from Recorder import Recorder
from AIUI_CMN import WEB_APPID, API_KEY, AUTH_ID

URL = "http://openapi.xfyun.cn/v2/aiui"
AUE = "raw"
DATA_TYPE = "audio"
SAMPLE_RATE = "16000"
SCENE = "main_box"
RESULT_LEVEL = "complete"
LAT = "31.278759"
LNG = "121.540805"
#个性化参数，需转义
PERS_PARAM = "{\\\"auth_id\\\":\\\"f87567f2159b425795ebb7ba9bc406ec\\\"}"
FILE_PATH = ""


class AIUIAgent(object):
    def __init__(self) -> None:
        super().__init__()
        self.url = URL
        self.auth_id = AUTH_ID
        self.api_key = API_KEY
        self.appid = WEB_APPID
        self.aue = AUE
        self.scene = SCENE
        self.sample_rate = SAMPLE_RATE
        self.lat = LAT
        self.lng = LNG

    def buildHeader(self, data_type, result_level='complete', pers_param=None):
        curTime = str(int(time.time()))
        param = {
            "result_level": result_level,
            "auth_id": self.auth_id,
            "data_type": data_type,
            "sample_rate": self.sample_rate,
            "scene": self.scene,
            "lat": self.lat,
            "lng": self.lng
        }
        if pers_param is not None:
            param["pers_param"] = pers_param
        param = json.dumps(param)
        paramBase64 = base64.b64encode(param.encode('utf8'))

        m2 = hashlib.md5()
        m2.update(self.api_key.encode('utf8') + curTime.encode('utf8') + paramBase64)
        checkSum = m2.hexdigest()

        header = {
            'X-CurTime': curTime,
            'X-Param': paramBase64,
            'X-Appid': self.appid,
            'X-CheckSum': checkSum,
        }
        return header

    def readFile(self, filePath):
        binfile = open(filePath, 'rb')
        data = binfile.read()
        return data
    
    def sendMessage(self, data_type, data):
        return requests.post(URL, headers=self.buildHeader(data_type=data_type), data=data)


if __name__ == '__main__':
    recorder = Recorder()
    total_audio_data, has_spoken = recorder.get_record_audio_with_vad()
    
    aiui_agent = AIUIAgent()
    if total_audio_data != b'':
        start = time.time()
        ret = aiui_agent.sendMessage(data_type="audio", data=total_audio_data)
        
        print(json.loads(ret.content))
        print(time.time() - start)  
    else:
        print('no audio input.')