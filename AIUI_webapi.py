#-*- coding: utf-8 -*-

import requests
import time
import hashlib
import base64
from rich import print
import json
import MSP_CMN
from Recorder import Recorder
from QISR import *

URL = "http://openapi.xfyun.cn/v2/aiui"
APPID = "93358e84"
API_KEY = "bd963c2e6087ac4106b563b725815470"
AUE = "raw"
AUTH_ID = 'f87567f2159b425795ebb7ba9bc406ec'
DATA_TYPE = "audio"
SAMPLE_RATE = "16000"
SCENE = "main_box"
RESULT_LEVEL = "complete"
LAT = "39.938838"
LNG = "116.368624"
#个性化参数，需转义
PERS_PARAM = "{\\\"auth_id\\\":\\\"f87567f2159b425795ebb7ba9bc406ec\\\"}"
FILE_PATH = ""


def buildHeader():
    curTime = str(int(time.time()))
    param = {
        "result_level": RESULT_LEVEL,
        "auth_id": AUTH_ID,
        "data_type": DATA_TYPE,
        "sample_rate": SAMPLE_RATE,
        "scene": SCENE,
        "lat": LAT,
        "lng": LNG,
        # "pers_param": PERS_PARAM    # 使用个性化参数
    }
    param = json.dumps(param)
    # param = "{\"result_level\":\""+RESULT_LEVEL+"\",\"auth_id\":\""+AUTH_ID+"\",\"data_type\":\""+DATA_TYPE+"\",\"sample_rate\":\""+SAMPLE_RATE+"\",\"scene\":\""+SCENE+"\",\"lat\":\""+LAT+"\",\"lng\":\""+LNG+"\"}"
    #使用个性化参数时参数格式如下：
    # param = "{\"result_level\":\""+RESULT_LEVEL+"\",\"auth_id\":\""+AUTH_ID+"\",\"data_type\":\""+DATA_TYPE+"\",\"sample_rate\":\""+SAMPLE_RATE+"\",\"scene\":\""+SCENE+"\",\"lat\":\""+LAT+"\",\"lng\":\""+LNG+"\",\"pers_param\":\""+PERS_PARAM+"\"}"
    paramBase64 = base64.b64encode(param.encode('utf8'))

    m2 = hashlib.md5()
    m2.update(API_KEY.encode('utf8') + curTime.encode('utf8') + paramBase64)
    checkSum = m2.hexdigest()

    header = {
        'X-CurTime': curTime,
        'X-Param': paramBase64,
        'X-Appid': APPID,
        'X-CheckSum': checkSum,
    }
    return header

def readFile(filePath):
    binfile = open(filePath, 'rb')
    data = binfile.read()
    return data



if __name__ == '__main__':
    msp_cmn = MSP_CMN()
    msp_cmn.Login()
 
    recorder = Recorder()

    isr = QISR(msp_cmn.dll, recorder, ASR_RES_PATH, GRM_FILE, GRM_BUILD_PATH)
    total_audio_data, has_spoken = recorder.get_record_audio_with_vad()
    
    start = time.time()
    r = requests.post(URL, headers=buildHeader(), data=total_audio_data)
    
    print(json.loads(r.content))
    print(time.time() - start)