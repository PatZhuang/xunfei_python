from ctypes import *
from Recorder import Recorder
from MSP_CMN import MSP_CMN
from MSP_TYPES import *
from rich import print
import traceback
import os
from utils import *
import time
import json
from params import args


ASR_RES_PATH        = "fo|res/asr/common.jet";  # 离线语法识别资源路径
GRM_BUILD_PATH      = "res/asr/GrmBuild";       # 构建离线语法识别网络生成数据保存路径
GRM_FILE            = "coffeebar.bnf";          # 构建离线识别语法网络所用的语法文件
MAX_GRAMMARID_LEN   = 32

SAMPLE_RATE_8K      = 8000
SAMPLE_RATE_16K     = 16000


class UserData(Structure):
    _fields_ = [
        ("build_fini", c_int),
        ("update_fini", c_int),
        ("errcode", c_int),
        ("grammar_id", c_char * 32)
    ]


class QISR(object):
    def __init__(self, dll: CDLL, recorder: Recorder, asr_res_path=None, grm_file=None, grm_build_path=None):
        super().__init__()
        self.dll = dll
        self.recorder = recorder
        self.asr_res_path = asr_res_path
        self.grm_build_path = grm_build_path
        self.grm_file = grm_file
        
        self.sessionID_local = c_void_p()
        self.sessionID_cloud = c_void_p()
        self._session_local_avail = False
        self._session_cloud_avail = False
        self.asr_data = UserData()
        self.ring = 0
        memset(addressof(self.asr_data), 0, sizeof(self.asr_data))
        
        # callback functions
        @CFUNCTYPE(c_int, c_int, c_char_p, c_void_p)
        def GrammarCallBack(error_code, info, user_data):
            #typedef int ( GrammarCallBack)(int errorCode, const char info, void* userData);
            grm_data = UserData.from_address(user_data)
            
            if user_data:    # check if userData is NULL (whose bool value is False in python)
                grm_data.build_fini = 1
                grm_data.errcode = error_code
                
            if MSP_SUCCESS == error_code and info is not None:
                print("构建语法成功！语法 ID: %s" % info.decode('utf-8'))
                grm_data.grammar_id = info
                return 1
            else:
                print("构建语法失败, error code: %d" % error_code)
                return 0
 
        self.pGrammarCallBackFunc = GrammarCallBack
        
        @CFUNCTYPE(c_int, c_int, c_char_p, c_void_p)
        def UpdateLexiconCallBack(errorCode, info, user_data):
            lex_data = UserData.from_address(user_data)
            
            if user_data:
                lex_data.update_fini = 1
                lex_data.errcode = errorCode
                
            if MSP_SUCCESS == errorCode:
                print("更新词典成功！")
                return 1
            else:
                print("更新词典失败！errcode: %d" % errorCode)
            
                return 0
        
        self.pUpdateLexCallBackFunc = UpdateLexiconCallBack
        
        self.set_arg_types()
        self.set_res_type()
        
        if args.build_grammar:
            self.BuildGrammar()
            while not self.asr_data.build_fini:
                time.sleep(2)
            if MSP_SUCCESS != self.asr_data.errcode:
                return
            print("离线识别语法网络构建完成，开始识别...")
        elif args.local_grammar:
            self.asr_data.grammar_id = bytes(args.local_grammar, encoding='utf8')
            print("开始识别...")
        else:
            raise RuntimeError("You should either build grammar or use existing local grammar.")
        
    def set_arg_types(self):
        self.dll.QISRBuildGrammar.argtypes = [c_char_p, c_char_p, c_uint, c_char_p, c_void_p, POINTER(UserData)]
        self.dll.QISRUpdateLexicon.argtypes = [c_char_p, c_char_p, c_uint, c_char_p, c_void_p, POINTER(UserData)]
        self.dll.QISRAudioWrite.argtypes = [c_char_p, c_void_p, c_uint, c_int, POINTER(c_int), POINTER(c_int)]
        self.dll.QISRGetResult.argtypes = [c_char_p, POINTER(c_int), c_int, POINTER(c_int)]
    
    def set_res_type(self):
        self.dll.QISRSessionBegin.restype = c_char_p
        self.dll.QISRGetResult.restype = c_char_p
    
    def SessionBeginLocal(self, result_type="json", asr_threshold=0, asr_denoise=1, vad_bos=5000, vad_eos=2000):
        begin_params = "engine_type=local,\
            asr_res_path={},grm_build_path={},\
            local_grammar={},\
            result_type={},reulst_encoding={},\
            asr_threshold={},asr_denoise={},vad_bos={},vad_eos={}".format(self.asr_res_path, self.grm_build_path,
                                          self.asr_data.grammar_id.decode('utf8'), result_type, "UTF-8" if result_type == 'json' else "gb2312",
                                          asr_threshold, asr_denoise, vad_bos, vad_eos)
        begin_params = bytes(begin_params, encoding='utf8')
        error_code = c_int()
        self.sessionID_local = self.dll.QISRSessionBegin(None, begin_params, byref(error_code))
        if MSP_SUCCESS != error_code.value:
            raise RuntimeError("QISRSessionBegin failed, error code: %d" % error_code.value)
        
        self._session_local_avail = True
            
    def SessionBeginCloud(self):
        pass
    
    def _SessionEndLocal(self, hints=None):
        hints = bytes(hints, encoding="utf8")
        ret = self.dll.QISRSessionEnd(self.sessionID_local, hints)
        if MSP_SUCCESS != ret:
            raise RuntimeError("QISRSessionEnd Error, errCode: %d" % ret)
        self.sessionID_local = c_void_p()
        self._session_local_avail = False
        
    def _SessionEndCloud(self, hints=None):
        pass
    
    def SessionEnd(self, sessionID, hints=None):
        if sessionID == self.sessionID_local:
            self._SessionEndLocal(hints)
        elif sessionID == self.sessionID_cloud:
            self._SessionEndCloud(hints)
        else:
            raise ValueError('Wrong sessionID')
    
    def BuildGrammar(self):
        print("构建离线识别语法网络...")
        
        assert self.grm_file is not None, "self.grm_file 为空"
        assert self.asr_res_path is not None, "self.asr_res_path 为空"
        assert self.grm_build_path is not None, "self.grm_build_path 为空"
 
        grm_content = None
        with open(self.grm_file, 'rb') as grm_file:
            grm_file.seek(0, 2)
            grm_content_len = grm_file.tell()
            grm_file.seek(0, 0)
            
            grm_content = grm_file.read(grm_content_len)
            
            grm_build_params = "engine_type=local,asr_res_path={},sample_rate={},grm_build_path={}".format(
                self.asr_res_path, SAMPLE_RATE_16K, self.grm_build_path
            )
            grm_build_params = bytes(grm_build_params, encoding='utf8')
            grammar_type = bytes("bnf", encoding='utf8')
            
            ret = self.dll.QISRBuildGrammar(grammar_type, grm_content, grm_content_len, grm_build_params, self.pGrammarCallBackFunc, byref(self.asr_data))
        if MSP_SUCCESS != ret:
            raise RuntimeError("Build grammar failed, error code: %d" % ret)
        return ret
    
    def UpdateLexicon(self, lex_name=None, lex_content=None):
        update_lex_params = "engine_type=local, text_encoding=UTF-8,\
            asr_res_path={}, sample_rate={},\
            grm_build_path={}, grammar_list={}".format(
                self.asr_res_path, SAMPLE_RATE_16K, self.grm_build_path, self.asr_data.grammar_id
            )
        lex_name = bytes(lex_name, encoding='utf8')
        lex_content = bytes(lex_content, encoding='utf8')
        lex_content_len = self.dll.strlen(lex_content)
        update_lex_params = bytes(update_lex_params, encoding='utf8')
        return self.dll.QISRUpdateLexicon(lex_name, lex_content, lex_content_len, update_lex_params, self.pUpdateLexCallBackFunc, byref(self.asr_data))
    
    def AudioWrite(self, sessionID, audio_data, audio_len, audio_status, ep_status, rec_status):
        ret = self.dll.QISRAudioWrite(sessionID, audio_data, audio_len, audio_status, byref(ep_status), byref(rec_status))
        if MSP_SUCCESS != ret:
            raise RuntimeError("QISRAudioWrite failed, error code: %d" % ret)
        
        return ret
    
    def GetResult(self, sessionID, result_type):
        error_code = c_int()
        result_status = c_int()
        wait_time = c_int(5000)
        total_result = ''
        
        while MSP_REC_STATUS_COMPLETE != result_status.value:
            rec_result = self.dll.QISRGetResult(sessionID, byref(result_status), c_int(), byref(error_code))
            if MSP_SUCCESS != error_code.value:
                print("QISRGetResult failed, error code: %d" % error_code.value)
            if type(rec_result) is bytes:
                if result_type == 'plain':
                    print(rec_result.decode('gb2312'))
                elif result_type == 'json':
                    print(json.loads(rec_result.decode('utf8')))
                
            time.sleep(0.2)

    def debug(self):
        self.run_asr(result_type='json')
        
    def run_asr(self, result_type='json'):
        self.SessionBeginLocal(result_type=result_type)
        audio_clip_cnt = 0
        ep_status = c_int(MSP_EP_LOOKING_FOR_SPEECH)
        rec_status = c_int(MSP_REC_STATUS_INCOMPLETE)
        rss_status = c_int(MSP_REC_STATUS_INCOMPLETE)
        
        while True:
            if 0 == audio_clip_cnt:
                audio_status = MSP_AUDIO_SAMPLE_FIRST
            else:
                audio_status = MSP_AUDIO_SAMPLE_CONTINUE
                
            audio_data = self.recorder.get_record_audio(duration=0.2)
            audio_len = len(audio_data)
            
            self.AudioWrite(self.sessionID_local, audio_data, audio_len, audio_status, ep_status, rec_status)
            if MSP_EP_AFTER_SPEECH == ep_status.value:
                break
        self.AudioWrite(self.sessionID_local, c_void_p(), 0, MSP_AUDIO_SAMPLE_LAST, ep_status, rec_status)
        self.GetResult(self.sessionID_local, result_type=result_type)
        self.SessionEnd(self.sessionID_local, hints="Done recognizing")
        
            
if __name__ == '__main__':
    msp_cmn = MSP_CMN()
    msp_cmn.Login()
 
    recorder = Recorder()

    isr = QISR(msp_cmn.dll, recorder, ASR_RES_PATH, GRM_FILE, GRM_BUILD_PATH)
    isr.debug()