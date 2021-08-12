from ctypes import *
import traceback


def read_charp_with_len(addr, length):
    """将 ctypes 的 POINTER 中的内容读出, 默认为字符串类型

    Args:
        addr (int): 指针首地址
        length (int): 字符串长度

    Raises:
        TypeError: 数据长度有误

    Returns:
        c_char_p: c_char_p 类型的 C 字符串首地址
    """
    if type(length) is not int:
        try:
            length = length.value
        except:
            traceback.print_exc()
            raise TypeError('Wrong length type')
        
    return (c_char * length).from_address(addr)