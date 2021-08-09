from ctypes import *
import traceback


def read_pointer(addr, length):
    if type(length) is not int:
        try:
            length = length.value
        except:
            traceback.print_exc()
            raise TypeError('Wrong length type')
        
    return (c_char * length).from_address(addr)