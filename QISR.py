from ctypes import *
from Recorder import Recorder
from MSP_CMN import MSP_CMN
from MSP_TYPES import *
from rich import print
from utils import *
import time
import json
from params import args


ASR_RES_PATH        = "fo|res/asr/common.jet";  # 离线语法识别资源路径
GRM_BUILD_PATH      = "res/asr/GrmBuild";       # 构建离线语法识别网络生成数据保存路径
GRM_FILE            = "coffeebar.bnf";          # 构建离线识别语法网络所用的语法文件
MAX_GRAMMARID_LEN   = 32


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
        self.sessionID = c_char_p()
        self._session_valid = False
        
        self.asr_data = UserData()
        memset(addressof(self.asr_data), 0, sizeof(self.asr_data))
        
        # callback functions
        @CFUNCTYPE(c_int, c_int, c_char_p, c_void_p)
        def BuildGrammarCallBack(error_code, info, user_data):
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
 
        self.build_grammar_cb = BuildGrammarCallBack
        
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
        
        self.update_lex_cb = UpdateLexiconCallBack
        
        self.set_arg_types()
        self.set_res_type()
        
        self.build_grm_params = {
            'engine_type':      'local',
            'sample_rate':      SAMPLE_RATE_16K,
            'asr_res_path':     ASR_RES_PATH,
            'grm_build_path':   GRM_BUILD_PATH
        }
        
        if args.build_grammar:
            self.BuildGrammar()
            while not self.asr_data.build_fini:
                time.sleep(2)
            if MSP_SUCCESS != self.asr_data.errcode:
                return
            print("离线识别语法网络构建完成，开始识别...")
        elif args.local_grammar:
            self.asr_data.grammar_id = args.local_grammar.encode('utf8')
            print("开始识别...")
        else:
            raise RuntimeError("Use '-bg' to build local grammar or use '-lg grammar_name' to specify existing local grammar.")
        
        self.begin_params = {                       # U 通用, L 离线, O 在线
            'engine_type':      'local' if args.sr_type == 'asr' else 'cloud',      # U 引擎类型: cloud, local
            'sub':              'asr' if args.sr_type == 'asr' else 'iat',          # O 本次识别请求的类型: iat (在线), asr (离线)
            'language':         'zh_cn',            # O 语言: zh_cn, en_us
            'domain':           'iat',              # O 领域
            'accent':           'mandarin',         # O 语言区域
            'sample_rate':      SAMPLE_RATE_16K,    # U 音频采样率
            'asr_threshold':    0,                  # L 识别门限: 0~100
            'asr_denoise':      1,                  # L 是否开启降噪
            'asr_res_path':     ASR_RES_PATH,       # L 离线识别资源路径
            'grm_build_path':   GRM_BUILD_PATH,     # L 离线语法生成路径
            'result_type':      'json',             # U 结果格式
            'text_encoding':    'UTF-8',            # U 参数文本编码格式
            'local_grammar':    self.asr_data.grammar_id.decode('utf8'),    # L 离线语法 ID
            'ptt':              1,                  # U 添加标点符号, 仅 sub=iat 时有效
            'aue':              'speex-wb;7',       # O 音频编码格式和压缩等级
            'result_encoding':  'UTF-8',            # U 识别结果字符串编码格式
            'vad_enable':       1,                  # U VAD 开关
            'vad_bos':          10000,              # U 允许头部静音的最长时间, 单位为毫秒, 仅打开 VAD 时有效
            'vad_eos':          2000                # U 允许尾部静音的最长时间, 单位为毫秒, 仅打开 VAD 时有效
        }
        
        self.update_lex_params = {
            'engine_type':      'local',            # U 引擎类型
            'subject':          'uup',              # O 业务类型
            'data_type':        'userword',         # O 数据类型
            'text_encoding':    'UTF-8',            # U 文本编码格式
            'sample_rate':      SAMPLE_RATE_16K,    # U 音频采样率
            'asr_res_path':     ASR_RES_PATH,       # L 离线识别资源路径
            'grm_build_parh':   GRM_BUILD_PATH,     # L 离线语法生成路径
            'grammar_list':     self.begin_params['local_grammar']      # L 语法 ID 列表, 支持一次性更新多个语法. 格式为 id1;id2
        }
        
    def set_arg_types(self):
        self.dll.QISRBuildGrammar.argtypes = [c_char_p, c_char_p, c_uint, c_char_p, c_void_p, POINTER(UserData)]
        self.dll.QISRUpdateLexicon.argtypes = [c_char_p, c_char_p, c_uint, c_char_p, c_void_p, POINTER(UserData)]
        self.dll.QISRAudioWrite.argtypes = [c_char_p, c_void_p, c_uint, c_int, POINTER(c_int), POINTER(c_int)]
        self.dll.QISRGetResult.argtypes = [c_char_p, POINTER(c_int), c_int, POINTER(c_int)]
    
    def set_res_type(self):
        self.dll.QISRSessionBegin.restype = c_char_p
        self.dll.QISRGetResult.restype = c_char_p
    
    def SessionBegin(self, params=None):
        """QISRSessionBegin, 开始一次语音识别。

        Args:
            params (dict or str, optional): SessionBegin 所需的参数. 默认使用 self.begin_params.

        Raises:
            RuntimeError: QISRSessionBegin failed

        Returns:
            bytes: sessionID
        """
        if not params:
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
        self.sessionID = self.dll.QISRSessionBegin(None, params, byref(error_code))
        if MSP_SUCCESS != error_code.value:
            raise RuntimeError("QISRSessionBegin failed, error code: %d" % error_code.value)
        self._session_valid = True
        
        return self.sessionID

    def AudioWrite(self, audio_data, audio_status):
        """QISRAudioWrite, 写入本次识别的音频。

        Args:
            audio_data (bytes or None): 音频字节流或 None
            audio_status (int): audioStatus, 告知 MSC 音频发送是否完成

        Raises:
            RuntimeError: QISRAudioWrite failed

        Returns:
            c_int: QISRAudioWrite 的引用参数 epStatus, 表示端点检测状态
            c_int: QISRAudioWrite 的引用淡出 rsltStatus, 表示识别器状态
        """
        ep_status = c_int()
        rslt_status = c_int()
        if audio_data is not None:
            audio_len = len(audio_data)
        else:
            audio_len = 0
        ret = self.dll.QISRAudioWrite(self.sessionID, audio_data, audio_len, audio_status, byref(ep_status), byref(rslt_status))
        if MSP_SUCCESS != ret:
            raise RuntimeError("QISRAudioWrite failed, error code: %d" % ret)
        
        return ep_status, rslt_status
    
    def GetResult(self):
        """QISRGetResult, 获取识别结果。

        Raises:
            RuntimeError: QISRGetResult failed

        Returns:
            c_char_p or None: 函数执行成功且有结果，返回字符串指针，否则返回 None
            c_int: QISRGetResult 的引用参数 rsltStatus, 表示识别器状态
        """
        error_code = c_int()
        rslt_status = c_int()
        wait_time = c_int(5000) # 保留参数, 未使用
        
        rec_result = self.dll.QISRGetResult(self.sessionID, byref(rslt_status), c_int(), byref(error_code))
        if MSP_SUCCESS != error_code.value:
            raise RuntimeError("QISRGetResult failed, error code: %d" % error_code.value)
        return rec_result, rslt_status

    def SessionEnd(self, hints="End session"):
        """QISRSessionEnd, 结束本次语音识别。

        Args:
            hints (str, optional): 结束本次语音识别的原因描述，为用户自定义内容. Defaults to "End session".

        Raises:
            RuntimeError: QISREndSession failed.
        """
        if hints is not None:
            hints = hints.encode('utf8')
        ret = self.dll.QISRSessionEnd(self.sessionID, hints)
        if MSP_SUCCESS != ret:
            raise RuntimeError("QISRSessionEnd Error, errCode: %d" % ret)
        self.sessionID = c_char_p()
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
        assert param_name in ["sid", "upflow", "downflow", "volumn"], "Wrong paramName"
        
        param_name = param_name.encode('utf8')
        param_value = (c_char * 32)()
        valueLen = c_int(32)
        
        ret = self.dll.QTTSGetParam(self.sessionID, param_name, param_value, byref(valueLen))

        if MSP_SUCCESS != ret:
            raise RuntimeError("QISRGetParam failed, error code: %d" % ret)
        return param_value.decode('utf8')

    def BuildGrammar(self, grammar_type='bnf', grammar_content=None, params=None, callback=None):
        """QISRBuildGrammar, 构建语法，生成语法ID。

        Args:
            grammar_type (str, optional): grammarType. Defaults to 'bnf'.
            grammar_content (bytes, optional): grammarContent. 默认读取 self.grm_file 中的文件内容
            params (dict or str, optional): 参数列表. 默认使用 self.build_grm_params
            callback (c_void_p, optional): 回调函数. 默认使用 self.build_grm_cb

        Raises:
            RuntimeError: QISRBuildGrammar failed

        Returns:
            UserData: QISRBuildGrammar 的引用参数 data
        """
        print("构建离线识别语法网络...")
        
        grammar_type = 'bnf'.encode('utf8') # 离线识别使用 bnf 语法
        if grammar_content is None:
            assert self.grm_file is not None, "grammar_content is None and no grm_file is found"
            with open(self.grm_file, 'rb') as grm_file:
                grm_file.seek(0, 2)
                grammar_length = grm_file.tell()
                grm_file.seek(0, 0)
                grammar_content = grm_file.read(grammar_length)
        else:
            grammar_length = self.dll.strlen(grammar_content)
        
        if params is None:
            params = self.build_grm_params
        if type(params) is dict:
            params = params_str_from_dict(params)
        if type(params) is str:
            params = params.encode('utf8')
        elif type(params) is bytes:
            params = params
        else:
            raise TypeError("Wrong params type.")
            
        if callback is None:
            callback = self.build_grammar_cb
            
        ret = self.dll.QISRBuildGrammar(grammar_type, grammar_content, grammar_length, params, callback, byref(self.asr_data))
        if MSP_SUCCESS != ret:
            raise RuntimeError("Build grammar failed, error code: %d" % ret)
        return self.asr_data
    
    def UpdateLexicon(self, lex_name, lex_content, params=None, callback=None):
        """QISRUpdateLexicon, 更新本地语法词典。

        Args:
            lex_name (str): lexiconName, 词典名称
            lex_content (str): lexiconContent, 词典内容
            params (dict or str, optional): 参数列表, 默认使用 self.update_lex_params
            callback (c_void_p, optional): 回调函数，默认使用 self.update_lex_cb

        Raises:
            RuntimeError: QISRUpdateLexicon failed

        Returns:
            UserData: QISRUpdateLexicon 的引用参数 data
        """
        # NOT TESTED!!!
        lex_name = lex_name.encode('utf8')
        lex_content = lex_content.encode('utf8')
        lex_content_len = self.dll.strlen(lex_content)
        
        if params is None:
            params = self.update_lex_params
        if type(params) is dict:
            params = params_str_from_dict(params)
        if type(params) is str:
            params = params.encode('utf8')
        elif type(params) is bytes:
            params = params
        else:
            raise TypeError("Wrong params type.")
            
        if callback is None:
            callback = self.update_lex_cb
        ret = self.dll.QISRUpdateLexicon(lex_name, lex_content, lex_content_len, params, callback, byref(self.asr_data))
        if MSP_SUCCESS != ret:
            raise RuntimeError("QISRUpdateLexicon failed, error code: %d" % ret)
        return self.asr_data
    
    def GetTotalResult(self, result_type='json'):
        """反复调用 GetResult 直到识别结束

        Args:
            result_type (str, optional): 与 SessionBegin 时传入的 result_encoding 参数相同

        Returns:
            list: 包含 GetResult 所有结果的列表
        """
        total_result = []
        status = c_int(2)
        while MSP_REC_STATUS_COMPLETE != status.value:
            rec_result, status = self.GetResult()
            if rec_result is not None:
                if result_type == 'plain':
                    total_result.append(json.loads(rec_result.decode('gb2312')))
                elif result_type == 'json':
                    total_result.append(json.loads(rec_result.decode('utf8')))
            else:
                time.sleep(0.2)
        return total_result
        
    def run_asr(self, sr_type="local", result_type='json'):
        """执行一次识别 (离线命令词和在线识别均可)

        Args:
            sr_type(srt, optional): 识别类型, local 为离线命令词识别, cloud 为在线识别
            result_type (str, optional): 与 SessionBegin 时传入的 result_encoding 参数相同

        Returns:
            list: GetTotalResult 的返回结果
            bytes: 本次识别读入的完整音频流
        """
        self.SessionBegin()
        audio_clip_cnt = 0
        
        total_audio_data = b''
        while True:
            if 0 == audio_clip_cnt:
                audio_status = MSP_AUDIO_SAMPLE_FIRST
            else:
                audio_status = MSP_AUDIO_SAMPLE_CONTINUE
            audio_clip_cnt += 1
                
            audio_data = self.recorder.get_record_audio(duration=1000)
            total_audio_data += audio_data
            
            ep_status, rstl_status = self.AudioWrite(audio_data, audio_status)
            if MSP_EP_AFTER_SPEECH == ep_status.value:
                break
        ep_status, rstl_status = self.AudioWrite(None, MSP_AUDIO_SAMPLE_LAST)
        if MSP_REC_STATUS_SUCCESS == rstl_status.value:
            print('识别成功, 获取结果中...')
        total_result = self.GetTotalResult(result_type=result_type)
        for res in total_result:
            print(res)
        self.SessionEnd(hints="Done recognizing")
        self.recorder.play_buffer(total_audio_data)
        return total_result, total_audio_data
        
            
if __name__ == '__main__':
    msp_cmn = MSP_CMN()
    msp_cmn.Login()
 
    recorder = Recorder()

    isr = QISR(msp_cmn.dll, recorder, ASR_RES_PATH, GRM_FILE, GRM_BUILD_PATH)
    isr.run_asr()