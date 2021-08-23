from ctypes import *
from struct import error
from Recorder import Recorder
from MSP_TYPES import *
from rich import print
import traceback
from utils import *
from MSP_CMN import MSP_CMN


IVW_THRESHOLD = '0:1450,1:1450,2:1450,3:1450'   # 唤醒词序号:唤醒阈值，请根据控制台的设置自行修改
JET_PATH = 'fo|res/ivw/wakeupresource.jet'


class QIVW(object):
    def __init__(self, dll: CDLL, recorder: Recorder) -> None:
        super().__init__()
        self.dll = dll
        self.recorder = recorder
        self.ivw_threshold = IVW_THRESHOLD
        self.jet_path = JET_PATH
        self.begin_params = {
            'sst': 'wakeup',
            'ivw_threshold': self.ivw_threshold,
            'ivw_res_path': self.jet_path
        }
        self.sessionID = c_char_p()
        self._session_valid = False # mark if sessionID is valid
        self.awoken = False
        
        # callback
        @CFUNCTYPE(None, c_char_p, c_uint64, c_uint64, c_uint64, c_void_p, c_void_p)
        def py_ivw_callback(sessionID, msg, param1, param2, info, userData):
            # typedef int( *i`vw_ntf_handler)( const char *sessionID, int msg, int param1, int param2, const void *info, void *userData );
            if MSP_IVW_MSG_ERROR == msg:
                print("MSP_IVW_MSG_ERROR errCode: %d" % param1)
                return
            elif MSP_IVW_MSG_WAKEUP == msg:
                # info 是唤醒结果首地址，param2 是结果长度，结合两者可以读出数据
                info_str = read_charp_with_len(info, param2).value.decode('utf-8')
                print("info =>", info_str)
            elif MSP_IVW_MSG_ISR_RESULT == msg:
                # 按照文档的描述，实际上 Linux 的 SDK 中无法使用 oneshot 模式唤醒
                # 也就是不能做 唤醒+识别 因此以下两个判断应该不会成立
                if param1 == MSP_REC_STATUS_SUCCESS:
                    raw_info = read_charp_with_len(info, param2)
                    info_str = b''.join(list(raw_info)).decode('utf-8')
                    print("info =>", info_str)
            elif MSP_IVW_MSG_ISR_EPS == msg:
                print("End-point detected status: %d" % param1)
            
            # 标记为已被唤醒
            self.awoken = True
                
        self.ivw_cb = py_ivw_callback
        self.set_arg_types()
        self.set_res_type()
        
    def set_arg_types(self):
        self.dll.QIVWSessionBegin.argtypes = [c_char_p, c_char_p, POINTER(c_int)]
        self.dll.QIVWSessionEnd.argtypes = [c_char_p, c_char_p]
        self.dll.QIVWRegisterNotify.argtypes = [c_char_p, c_void_p, c_void_p]
        self.dll.QIVWAudioWrite.argtypes = [c_char_p, c_void_p, c_uint64, c_int64]
        
    def set_res_type(self):
        self.dll.QIVWSessionBegin.restype = c_char_p
        
    def SessionBegin(self, params=None):
        """QIVWSessionBegin, 唤醒功能，并在参数中指定唤醒(唤醒+识别时)用到的语法列表，本次唤醒所用的参数等。

        Args:
            params (dict or str, optional): params 参数. 默认使用 self.begin_params

        Raises:
            RuntimeError: QIVWSessionBegin failed.

        Returns:
            str: SessionID
        """
        if params is None:
            params = self.begin_params

        if type(params) is dict:
            params = params_str_from_dict(params)
        if type(params) is str:
            params = params.encode('utf8')
        elif type(params) is bytes:
            params = params
        else:
            raise TypeError("Wrong params type.")
        
        error_code = c_int()
        self.sessionID = self.dll.QIVWSessionBegin(None, params, byref(error_code))
        if MSP_SUCCESS != error_code.value:
            raise RuntimeError("QIVWSessionBegin failed, error code %d" % error_code.value)
        self._session_valid = True
        return self.sessionID.decode('utf8')
        
    def RegisterNotify(self, sessionID=None, msg_proc_cb=None, user_data=None):
        """QIVWRegisterNotify, 注册回调。

        Args:
            sessionID (bytes, optional): sessionID. 默认使用 self.sessionID
            msg_proc_cb (c_void_p, optional): 回调函数. 默认使用 self.ivw_cb
            user_data (UserData, optional): 用户数据. Defaults to None.

        Raises:
            RuntimeError: [description]
        """
        if not sessionID:
            sessionID = self.sessionID
        assert sessionID is not None, 'SessionID is None'
        if not msg_proc_cb:
            msg_proc_cb = self.ivw_cb
        ret = self.dll.QIVWRegisterNotify(sessionID, msg_proc_cb, user_data)
        if MSP_SUCCESS != ret:
            raise RuntimeError("QIVWRegisterNotify failed, error code: %d" % ret)
        
    def AudioWrite(self, audio_data, audio_status=2):
        """QIVWAudioWrite, 写入本次唤醒的音频，本接口需要反复调用直到音频写完为止。

        Args:
            audioData (bytes): 要写入的音频数据
            audio_status (int, optional): 用来告知MSC音频发送是否完成. Defaults to 2.

        Raises:
            RuntimeError: [description]
        """
        audio_len = len(audio_data)        
        ret = self.dll.QIVWAudioWrite(self.sessionID, audio_data, audio_len, audio_status)
        if MSP_SUCCESS != ret:
            raise RuntimeError("QIVWAudioWrite failed, errCode: %d", ret)
        
    def SessionEnd(self, hints="Done wakeup"):
        """QIVWSessionEnd, 结束本次语音唤醒。

        Args:
            hints (str, optional): 结束本次语音唤醒的原因描述，为用户自定义内容. Defaults to "Done wakeup".

        Raises:
            RuntimeError: QIVWSessionEnd failed
        """
        if type(hints) is str:
            hints = hints.encode('utf8')
        ret = self.dll.QIVWSessionEnd(self.sessionID, hints)
        if MSP_SUCCESS != ret:
            raise RuntimeError("QIVWSessionEnd Error, errCode: %d" % ret)
        self.sessionID = c_char_p()
        self._session_valid = False
        
    def wakeup(self):
        """一次完整的唤醒流程

        Returns:
            bool: 是否正确结束本次唤醒
        """
        try:
            self.SessionBegin()
            self.RegisterNotify()
            self.recorder.start()
            while not self.awoken:
                audioData = self.recorder.get_record_audio()
                audioLen = len(audioData)
                self.AudioWrite(audioData)
            self.recorder.play_file('resources/wakeup.wav')
            self.awoken = False
            
            self.SessionEnd()
            return True
        except RuntimeError as e:
            traceback.print_exc() 
            return False
    
    def debug(self):
        """连续测试唤醒
        """
        while True:
            self.wakeup()
            
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
    vw = QIVW(msp_cmn.dll, recorder)
    vw.debug()