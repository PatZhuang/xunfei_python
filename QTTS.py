from ctypes import *
import threading
from Recorder import Recorder
from MSP_TYPES import *
from rich import print
import traceback
from utils import *
from MSP_CMN import MSP_CMN


class QTTS(object):
    def __init__(self, dll: CDLL, recorder: Recorder):
        super().__init__()
        self.dll = dll
        self.recorder = recorder

        self._session_avail = False
        self.sessionID = c_void_p()
        
        self.set_arg_types()
        self.set_res_type()
        
    def set_arg_types(self):
        self.dll.QTTSGetParam.argtypes = [c_char_p, c_char_p, c_char_p, POINTER(c_int)]
        
    def set_res_type(self):
        self.dll.QTTSSessionBegin.restype = c_char_p
        self.dll.QTTSAudioGet.restype = c_void_p

    def SessionBegin(self, engine_type="purextts", voice_name="xiaoyan", 
                     speed=50, volumn=50, pitch=50, rdn=0, rcn=0, 
                     text_encoding="UTF8", sample_rate=16000, background_sound=0,
                     aue="speex-wb;7", ttp="text", speed_increase=1, effect=0):

        beginParams = "engine_type={},voice_name={},speed={},volumn={},pitch={},rdn={},text_encoding={},sample_rate={},".format(
                engine_type, voice_name,speed, volumn, pitch, rdn, text_encoding, sample_rate
            )
  
        if engine_type == "cloud":
            beginParams += "background_sound={},aue={},ttp={}".format(background_sound, aue, ttp)
        else:
            if engine_type == "purextts":
                tts_res_path = "fo|res/xtts/{}.jet;fo|res/xtts/common.jet".format(voice_name)
            elif engine_type == "local":
                tts_res_path = "fo|res/tts/{}.jet;fo|res/tts/common.jet".format(voice_name)
            beginParams += "tts_res_path={},rcn={},speed_increase={},effect={}".format(
                tts_res_path, rcn, speed_increase, effect
                )
        beginParams = bytes(beginParams, encoding="utf8")
        errorCode = c_int64()
        
        self.sessionID = self.dll.QTTSSessionBegin(beginParams, byref(errorCode))
        if MSP_SUCCESS != errorCode.value:
            raise RuntimeError("QTTSSessionBegin failed, error code: %d" % errorCode.value)
        self._session_avail = True
        
        return self.sessionID

    def TextPut(self, textString=None):
        if textString is None:
            textString = "您好，我是迎宾机器人花生，请问您有什么需要？"
        textString = bytes(textString, encoding='utf8')
        textLen = self.dll.strlen(textString)
        ret = self.dll.QTTSTextPut(self.sessionID, textString, textLen, None)
        if MSP_SUCCESS != ret:
            raise RuntimeError("QTTSTextPut failed, error code: %d" % ret)
        
        return ret

    def AudioGet(self):
        audioLen = c_uint()
        synthStatus = c_int64()
        errorCode = c_int64()
        data = c_void_p()
        
        frames = []
        while True:
            data = self.dll.QTTSAudioGet(self.sessionID, byref(audioLen), byref(synthStatus), byref(errorCode))
            if data is not None:
                frames.append(read_pointer(data, audioLen).raw)
            if MSP_TTS_FLAG_DATA_END == synthStatus.value:
                break
        return b''.join(frames)
            
    def SessionEnd(self):
        hints = "Done TTS"
        hints = bytes(hints, encoding="utf8")
        ret = self.dll.QTTSSessionEnd(self.sessionID, hints)
        if MSP_SUCCESS != ret:
            raise RuntimeError("QTTSSessionEnd failed, errCode: %d" % ret)
        self.sessionID = c_void_p()
        self._session_avail = False

    def GetParam(self, paramName=None):
        # NOT WORKING!!!
        assert paramName in ["sid", "upflow", "downflow", "ced"], "Wrong paramName"
        
        paramName = bytes(paramName, encoding="utf8")
        paramValue = (c_char * 32)()
        valueLen = c_int(32)
        
        ret = self.dll.QTTSGetParam(self.sessionID, paramName, paramValue, byref(valueLen))

        if MSP_SUCCESS != ret:
            raise RuntimeError("QTTSGetParam failed, error code: %d" % ret)
        return paramValue

    def debug(self, textString=None):
        try:
            self.SessionBegin()
            self.TextPut(textString)
            audio = self.AudioGet()
            self.recorder.play_buffer(audio)
            self.SessionEnd()
        except (RuntimeError, ValueError) as e:
            traceback.print_exc()
            
    def say(self, textString=None, block=True):
        try:
            self.SessionBegin()
            self.TextPut(textString)
            if block:   # 阻塞交互，半双工
                self.recorder.abort()
                audio = self.AudioGet()
                self.recorder.play_buffer(audio)
            else:
                pass    
            self.SessionEnd()
        except (RuntimeError, ValueError) as e:
            traceback.print_exc()
        
    
    def __del__(self):
        if self._session_avail:
            try:
                self.SessionEnd()
            except RuntimeError as e:
                traceback.print_exc()  


if __name__ == '__main__':
    msp_cmn = MSP_CMN()
    msp_cmn.Login()
    
    recorder = Recorder()
    tts = QTTS(msp_cmn.dll, recorder)
    tts.debug()