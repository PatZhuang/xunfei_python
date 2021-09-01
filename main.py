from QIVW import QIVW
from QTTS import QTTS
from AIUI_webapi import AIUIAgent
from ctypes import *
from MSP_CMN import *
from Recorder import Recorder
import json
from rich import print


msp_cmn = MSP_CMN()
msp_cmn.Login()
recorder = Recorder()
ivw = QIVW(msp_cmn.dll, recorder)
tts = QTTS(msp_cmn.dll, recorder)
aiui_agent = AIUIAgent()


def order(slots):
    print(slots)
    tts.say('好的，这就为您下单。祝您用餐愉快。')


if __name__ == '__main__':
    while True:
        print('ready to be waken up')
        semantic = []
        if ivw.wakeup():    # 唤醒
            service = None
            while True:
                recorder.abort()
                total_audio_data, has_spoken = recorder.get_record_audio_with_vad()
        
                if has_spoken: # 输入音频不为空
                    ret = aiui_agent.sendMessage(data_type="audio", data=total_audio_data)
                    ret_data = json.loads(ret.content)['data']
                    try:
                        nlp_res = list(filter(lambda x:x['sub'] == 'nlp', ret_data))[0]
                        answer = nlp_res['intent']['answer']['text']
                        service = nlp_res['intent']['service'].split('.')[-1]
                        if service == 'peanut_daily' and not nlp_res['intent']['shouldEndSession']:
                            semantic = nlp_res['intent']['semantic']
                    except:
                        if service == 'peanut_daily':   # 如果识别出错但是处于点餐阶段，默认回复是的
                            ret = aiui_agent.sendMessage(data_type="text", data="是的")
                            ret_data = json.loads(ret.content)['data']
                            nlp_res = list(filter(lambda x:x['sub'] == 'nlp', ret_data))[0]
                            answer = nlp_res['intent']['answer']['text']
                            service = None
                            # order(semantic[0]['slots'])
                        else:
                            service = None
                            answer = "我没有听懂，可以请您再说一遍吗？"
                            print(ret_data)
                    finally:
                        print(ret_data)
                else:
                    if service == 'peanut_daily':
                        # 如果没有输入音频但是处于点餐阶段，默认回复是的
                        ret = aiui_agent.sendMessage(data_type="text", data="是的")
                        ret_data = json.loads(ret.content)['data']
                        nlp_res = list(filter(lambda x:x['sub'] == 'nlp', ret_data))[0]
                        answer = nlp_res['intent']['answer']['text']
                        service = None
                        # order(semantic[0]['slots'])
                    else:
                        print('no audio input')
                        break
                
                tts.say(answer)
                
            print('end session')
            recorder.play_file('resources/sleep.wav')
            
            
        