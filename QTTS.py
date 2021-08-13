from ctypes import *
from os import EX_CONFIG
from threading import setprofile
from Recorder import Recorder
from MSP_TYPES import *
from rich import print
import traceback
from utils import *
from MSP_CMN import MSP_CMN


VOICE_NAME = 'xiaoyan'
PUREXTTS_RES_PATH = "fo|res/xtts/{}.jet;fo|res/xtts/common.jet".format(VOICE_NAME)
TTS_RES_PATH = "fo|res/tts/{}.jet;fo|res/tts/common.jet".format(VOICE_NAME)

class QTTS(object):
    def __init__(self, dll: CDLL, recorder: Recorder):
        super().__init__()
        self.dll = dll
        self.recorder = recorder

        self._session_valid = False
        self.sessionID = c_void_p()
        self.begin_params = {               # U 通用, L 离线, O 在线
            'engine_type':  'purextts',     # U 引擎类型: purextts, local, cloud
            'voice_name':   VOICE_NAME,     # U 发言人
            'speed':        50,             # U 语速
            'volumn':       50,             # U 音量
            'pitch':        50,             # U 语调
            'tts_res_path': PUREXTTS_RES_PATH,   # L 合成资源路径
            'rdn':          0,              # U 数字发音
            'rcn':          1,              # L 1 的中文发音
            'text_encoding':    'UTF8',     # U 合成文本编码格式
            'sample_rate':  16000,          # U 合成音频采样率
            'background_sound': 0,          # O 合成音频中的背景音
            'aue':          'speex-wb;7',   # O 音频编码格式和压缩等级
            'ttp':          'text',         # O 文本类型
            'speed_increase':   1,          # L 语速增强
            'effect':       0               # L 合成音效
        }
        
        self.set_arg_types()
        self.set_res_type()
        
    def set_arg_types(self):
        self.dll.QTTSSessionBegin.argtypes = [c_char_p, POINTER(c_int)]
        self.dll.QTTSTextPut.argtypes = [c_char_p, c_char_p, c_uint, c_char_p]
        self.dll.QTTSAudioGet.argtypes = [c_char_p, POINTER(c_uint), POINTER(c_int), POINTER(c_int)]
        self.dll.QTTSSessionEnd.argtypes = [c_char_p, c_char_p]
        self.dll.QTTSGetParam.argtypes = [c_char_p, c_char_p, c_char_p, POINTER(c_int)]
        
    def set_res_type(self):
        self.dll.QTTSSessionBegin.restype = c_char_p
        self.dll.QTTSAudioGet.restype = c_void_p
        self.dll.QTTSGetParam.restype = c_char_p

    def SessionBegin(self, params=None):
        """QTTSSessionBegin, 开始一次语音合成，分配语音合成资源。

        Args:
            params (dict or str, optional): QTTSSessionBegin 的参数. 可以传入字典或字符串，默认使用 self.begin_params

        Raises:
            RuntimeError: SessionBegin failed.

        Returns:
            bytes: sessionID
        """
        if not params:
            params = self.begin_params
        if type(params) is dict:
            params = ','.join(['{}={}'.format(k, v) for k, v in params.items()])
        begin_params = params.encode('utf8')
        error_code = c_int()
        
        self.sessionID = self.dll.QTTSSessionBegin(begin_params, byref(error_code))
        if MSP_SUCCESS != error_code.value:
            raise RuntimeError("QTTSSessionBegin failed, error code: %d" % error_code.value)
        self._session_valid = True
        
        return self.sessionID

    def TextPut(self, text_string=None):
        """QTTSTextPut, 写入要合成的文本。

        Args:
            text_string (str, optional): 需要合成的文本. Defaults to None.

        Raises:
            RuntimeError: QTTSTextPut failed
        """
        if text_string is None:
            text_string = "您好，我是花生。"
        text_string = bytes(text_string, encoding='utf8')
        text_len = self.dll.strlen(text_string)
        ret = self.dll.QTTSTextPut(self.sessionID, text_string, text_len, None)
        if MSP_SUCCESS != ret:
            raise RuntimeError("QTTSTextPut failed, error code: %d" % ret)

    def AudioGet(self):
        """QTTSAudioGet, 获取合成音频。不同于官方实现，该函数会获取完整的合成音频并一起返回。

        Returns:
            bytes: 完整的合成音频 (此时 synth_status 为 MSP_TTS_FLAG_DATA_END)
        """
        audio_len = c_uint()
        synth_status = c_int()
        error_code = c_int()
        data = c_void_p()
        
        frames = []
        while True:
            data = self.dll.QTTSAudioGet(self.sessionID, byref(audio_len), byref(synth_status), byref(error_code))
            if data is not None:
                frames.append(read_charp_with_len(data, audio_len).raw)
            if MSP_TTS_FLAG_DATA_END == synth_status.value:
                break
        return b''.join(frames)
            
    def SessionEnd(self):
        """QTTSSessionEnd, 结束本次语音合成。

        Raises:
            RuntimeError: QTTSSessionEnd failed
        """
        hints = "Done TTS"
        hints = bytes(hints, encoding="utf8")
        ret = self.dll.QTTSSessionEnd(self.sessionID, hints)
        if MSP_SUCCESS != ret:
            raise RuntimeError("QTTSSessionEnd failed, errCode: %d" % ret)
        self.sessionID = c_void_p()
        self._session_valid = False

    def GetParam(self, param_name=None):
        """QTTSGetparam, 获取当前语音合成信息，如当前合成音频对应文本结束位置、上行流量、下行流量等。

        Args:
            param_name (str, optional): paramName 参数名. Defaults to None.

        Raises:
            RuntimeError: QTTSGetparam failed
            
        Returns:
            str: 参数值
        """
        # NOT WORKING!!!
        assert param_name in ["sid", "upflow", "downflow", "ced"], "Wrong paramName"
        
        param_name = bytes(param_name, encoding="utf8")
        param_value = (c_char * 32)()
        valueLen = c_int(32)
        
        ret = self.dll.QTTSGetParam(self.sessionID, param_name, param_value, byref(valueLen))

        if MSP_SUCCESS != ret:
            raise RuntimeError("QTTSGetParam failed, error code: %d" % ret)
        return param_value.decode('utf8')
            
    def say(self, text_string=None, block=True):
        """执行一次语音合成并通过扬声器播放合成音频

        Args:
            text_string (str, optional): 要合成的文本. Defaults to None.
            block (bool, optional): 播放音频时是否阻塞交互. Defaults to True.
        """
        try:
            self.SessionBegin()
            self.TextPut(text_string)
            if block:   # 阻塞交互，半双工
                self.recorder.abort()
                audio = self.AudioGet()
                self.recorder.play_buffer(audio)
            else:
                # 全双工交互暂未实现
                pass    
            self.SessionEnd()
        except (RuntimeError, ValueError) as e:
            traceback.print_exc()
        
    def __del__(self):
        if self._session_valid:
            try:
                self.SessionEnd()
            except RuntimeError as e:
                traceback.print_exc()  


if __name__ == '__main__':
    msp_cmn = MSP_CMN()
    msp_cmn.Login()
    
    recorder = Recorder()
    tts = QTTS(msp_cmn.dll, recorder)
    tts.say()