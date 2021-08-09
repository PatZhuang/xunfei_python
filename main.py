from QIVW import QIVW
from QTTS import QTTS
from ctypes import *
from StatusCode import *
from Recorder import Recorder

if __name__ == '__main__':
    msc_load_library = "../sdk/libs/x64/libmsc.so"
    dll = cdll.LoadLibrary(msc_load_library)
    
    app_id = 'a1500789'
    loginParams = "appid={}".format(app_id)
    loginParams = bytes(loginParams, encoding="utf8")
    ret = dll.MSPLogin(None, None, loginParams)
    if MSP_SUCCESS != ret:
        print("MSPLogin failed, error code is: %d", ret)
    
    recorder = Recorder()
    vw = QIVW(dll, recorder)
    tts = QTTS(dll, recorder)
    while True:
        if vw.wakeup():
            tts.debug()
            
        