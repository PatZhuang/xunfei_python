from ctypes import *
from utils import read_pointer
from MSP_TYPES import *
from rich import print
import traceback

MSC_LOAD_LIBRARY = "../sdk/libs/x64/libmsc.so"
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
        
    def Login(self):
        loginParams = "appid={}".format(self.appID)
        loginParams = bytes(loginParams, encoding="utf8")
        ret = self.dll.MSPLogin(None, None, loginParams)
        
        if MSP_SUCCESS != ret:
            raise RuntimeError("MSPLogin failed, error code is: %d", ret)
    
    def Logout(self):
        self.dll.MSPLogout()
    
    def SetParam(self, params_name, params_value):
        if type(params_name) is not bytes:
            params_name = bytes(params_name, encoding='utf8')
        if type(params_value) is not bytes:
            params_value = bytes(params_value, encoding='utf8')
        ret = self.dll.MSPSetParam(params_name, params_value)
        if MSP_SUCCESS != ret:
            raise RuntimeError("MSPSetParam failed, error code: %d" % ret)
            
    def GetParam(self, param_name):
        if type(param_name) is not bytes:
            param_name = bytes(param_name, encoding='utf8')
        param_value = c_char_p()
        param_len = c_int()
        ret = self.dll.MSPGetParam(param_name, param_value, byref(param_len))
        if MSP_SUCCESS != ret:
            raise RuntimeError("MSPGetParam failed, error code: %d" % ret)
        return read_pointer(param_value, param_len)
    
    
    def GetVersion(self, ver_name):
        pass