from ctypes import *
from utils import read_pointer
from MSP_TYPES import *
import json
from rich import print

MSC_LOAD_LIBRARY = "libs/x64/libmsc.so"
APP_ID = 'a1500789'

class MSP_CMN(object):
    def __init__(self, dll_path=None, appID=None):
        super().__init__()
        if dll_path is None:
            dll_path = MSC_LOAD_LIBRARY
        if appID is None:
            appID = APP_ID
        self.dll = cdll.LoadLibrary(dll_path)
        self.appID = appID
        self.set_arg_types()
        self.set_res_type()
        
    def set_arg_types(self):
        self.dll.MSPGetVersion.argtypes = [c_char_p, POINTER(c_int)]
        self.dll.MSPUploadData.argtypes = [c_char_p, c_void_p, c_uint, c_char_p, POINTER(c_int)]
    
    def set_res_type(self):
        self.dll.MSPGetVersion.restype = c_char_p
    
    def Login(self):
        loginParams = "appid={}".format(self.appID)
        loginParams = bytes(loginParams, encoding="utf8")
        ret = self.dll.MSPLogin(None, None, loginParams)
        if MSP_SUCCESS != ret:
            raise RuntimeError("MSPLogin failed, error code is: %d", ret)
        return ret
    
    def UploadData(self, data_name, data, params):
        # NOT TESTED.
        if type(data_name) is not bytes:
            data_name = data_name.encode('utf8')
        data_len = self.dll.strlen(data)
        if type(params) is dict:
            params = json.dumps(params)
        if type(params) is str:
            params = params.encode('utf8')
        error_code = c_int()
        ret = self.dll.MSPUploadData(data_name, data, data_len, params, byref(error_code))
        if MSP_SUCCESS != error_code.value:
            raise RuntimeError('MSPUploadData failed. error code: %d' % error_code.value)
        return error_code.value, ret
        
    
    def Logout(self):
        ret = self.dll.MSPLogout()
        if MSP_SUCCESS != ret:
            raise RuntimeError("MSPLogout failed, error code is: %d", ret)
        return ret
    
    def SetParam(self, params_name, params_value):
        if type(params_name) is not bytes:
            params_name = bytes(params_name, encoding='utf8')
        if type(params_value) is not bytes:
            params_value = bytes(params_value, encoding='utf8')
        ret = self.dll.MSPSetParam(params_name, params_value)
        if MSP_SUCCESS != ret:
            raise RuntimeError("MSPSetParam failed, error code: %d" % ret)
        return ret
            
    def GetParam(self, param_name):
        # NOT WORKING!!!
        if type(param_name) is not bytes:
            param_name = param_name.encode('utf8')
        if param_name.decode('utf8') not in ['upflow', 'downflow']:
            raise ValueError("param_name can only be 'upflow' or 'downflow'.")
        param_value = c_char_p()
        param_len = c_int()
        ret = self.dll.MSPGetParam(param_name, param_value, byref(param_len))
        if MSP_SUCCESS != ret:
            raise RuntimeError("MSPGetParam failed, error code: %d" % ret)
        return ret, read_pointer(param_value, param_len)
    
    def GetVersion(self, ver_name):
        if type(ver_name) is not bytes:
            ver_name = ver_name.encode('utf8')
        if ver_name.decode('utf8') not in ['ver_msc', 'ver_asr', 'ver_tts', 'ver_ivw']:
            raise ValueError("ver_name can only be: 'ver_msc', 'ver_asr', 'ver_tts' or 'ver_ivw'")
        error_code = c_int()
        ret = self.dll.MSPGetVersion(ver_name, byref(error_code))
        if MSP_SUCCESS != error_code.value:
            raise RuntimeError("MSPGetVersion failed. error code: %d" % error_code.value)
        return error_code.value, ret.decode('utf8')
        
if __name__ == '__main__':
    msp = MSP_CMN()
    print("MSPLogin: %d" % msp.Login())