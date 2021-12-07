## 项目简介

 x86/x64 平台讯飞 SDK & AIUI 的 python 接口

 基于 x86/x64 Linux SDK: 语音唤醒, 离线命令词识别, 在线语音识别, 离线/在线语音合成

 基于 WebAPI: AIUI 平台交互

## 准备工作

### 讯飞 SDK

> 只使用 AIUI WebAPI 接口的可以跳过这一步

1. 在[讯飞控制台](https://console.xfyun.cn)创建一个 `Linux` 平台的应用

2. 下载 Linux 平台的 [SDK](https://www.xfyun.cn/sdk/dispatcher). 本项目支持的 AI 能力有: 离线命令词识别, 离线语音合成(普通版/高品质版), 语音唤醒, 语音听写(流式版), 在线语音合成(流式版). (AIUI 基于 WebAPI, 不使用 SDK)

3. 解压 SDK 到 `xunfei_SDK` 目录, 将其中的 `libs` 和 `msc` 文件夹软链接到本工程根目录下, 并将动态链接库复制到系统路径:

```bash
cd ~

# 下载并解压 SDK, <...> 内容自行修改
unzip <SDK>.zip -d xunfei_SDK

git clone https://github.com/PatZhuang/xunfei_python.git
cd xunfei_python
# 软链接
# 假设 SDK 解压到了 ~/xunfei_SDK 请根据实际情况自行修改
ln -s ~/xunfei_SDK/bin/msc .
ln -s ~/xunfei_SDK/libs .
# 动态链接库复制到系统路径, 以 x64 为例
sudo cp ~/xunfei_SDK/libs/x64/*.so /usr/bin
sudo cp ~/xunfei_SDK/libs/x64/*.so /usr/local/bin
# 设置动态运行库查找路径, 请根据自己的终端类型和 SDK 路径自行修改, 这里以 bash 为例
echo "export LD_LIBRARY_PATH=$HOME/xunfei_SDK/libs/x64/" >> ~/.bashrc
source ~/.bashrc
```

4. 修改 APPID

将 `MSP_CMN.py` 中的 `APP_ID` 修改为自己的 APPID

### Python 相关依赖

本工程基于 python 3.9.6, 理论上 python 版本 >= 3.6 都能运行. 所需的依赖在 `requirements.txt` 中

```bash
pip install -r requirements.txt
pip install numpy   # Recorder 需要
```

> python 3.5 以下需要将 `rich` 库的引用全部删除 (不影响功能). 其他库的兼容性请自行测试.

### AIUI

AIUI 使用 WebAPI 接口而不是原生 SDK, 需要在 [AIUI 开放平台](https://aiui.xfyun.cn/app/add) 另外创建一个类型为 WebAPI 的应用.

在本工程根目录新建一个 `AIUI_CMN.py 文件`, 内容根据自己的 APP 信息填写:

```python
import hashlib

md5 = hashlib.md5()
md5.update(b"anything you want to hash")
AUTH_ID = md5.hexdigest()   # AUTH_ID 是一个任意的 MD5 串, 可以生成一次以后固定下来

WEB_APPID = "xxx"   # WebAPI 平台
API_KEY = "xxx"     # WebAPI 平台
```

## 功能简介

参考: [MSC_API 文档](https://www.xfyun.cn/doc/mscapi/Windows&Linux/wlapi.html)

> 以下调用示例均使用麦克风输入音频

### MSP_CMN.py

对应讯飞 SDK 中的 `msp_cmn.h`, 实现为一个同名的类 `MSP_CMN`. 使用时需要构造一个 `MSP_CMN` 对象.

```python
# 调用示例
from MSP_CMN import MSP_CMN

# 相当于 C 函数中执行了 MSPLogin()

msp_cmn = MSP_CMN() # 需要先初始化一个 MSP_CMN 的实例
msp_cmn.Login()     # 调用对应函数
```

### 语音唤醒 QIVW.py

对应讯飞 SDK 中的 `qivw.py`, 实现为一个同名的类 `QIVW`. 使用时需要构造一个 `QIVW` 对象.

请在讯飞控制台设置好唤醒词后再生成 SDK, 否则无法使用离线唤醒功能.

```python
# 运行一次语音唤醒
python QIVW.py
```

### 语音识别 QISR.py

对应讯飞 SDK 中的 `qisr.py`, 实现为一个同名的类 `QISR`. 使用时需要构造一个 `QISR` 对象.

1. 离线命令词识别:

请参考 [语法开发指南](http://bbs.xfyun.cn/thread/7595) 构造本地语法文件 `xxx.bnf` 并替换 `QISR.py` 中的 `GRM_FILE` 变量

第一次运行离线命令词识别前需要使用 `--build_grammar` 或 `-bg` 参数构建本地语法网络, 之后运行时可以使用 `--local_grammar xxx` 或 `-lg xxx` 参数加载本地语法. 具体查看 `params.py`.

```bash
# 先构造本地语法, 然后执行命令词识别
python QISR.py -bg

# or
# 指定本地语法文件, 然后执行命令词识别
# <local_grammar> 是 bnf 文件中第二行 !grammar 字段的值
python QISR.py -lg <local_grammar>
```

2. 在线识别:

```bash
# 从麦克风输入声音并识别
python QISR.py --sr_type iat
```

### 语音合成 QTTS.py

对应讯飞 SDK 中的 `qtts.py`, 实现为一个同名的类 `QTTS`. 使用时需要构造一个 `QTTS` 对象.

```bash
python QTTS.py --tts_text "要合成的文本"
```

### AIUI_webapi.py

`AIUI_webapi.py` 是 AIUI 的 webapi 接口的实现. 具体请参考: [WebAPI 接口文档](https://aiui.xfyun.cn/doc/aiui/develop/more_doc/webapi/summary.html)

> 注意 AIUI WebAPI 不支持流式识别, 需要一次性上传完整的音频.

```bash
# 调用 AIUI WebAPI, 通过麦克风输入音频(自动检测端点并截断), 获取语音识别返回结果
python AIUI_webapi.py
```

### Recorder.py

基于 [sounuddevice](https://python-sounddevice.readthedocs.io/en/0.4.2/) 的音频接口实现. 功能包含: 播放本地音频, 播放内存中的数据, 音频录制, 端点检测 (使用 [webrtcvad](https://github.com/wiseman/py-webrtcvad))

## 接口说明

### C 函数与 python 方法的对应

C 的头文件对应一个同名的 python 文件的一个同名类. 

例如 `qisr.h` 对应 `QISR.py` 的 `QISR` 类. 访问 `qisr.h` 的函数需要实例化一个 python 的 `QISR` 对象, 并使用其实例方法.

方法名也是一一对应的, 例如 C 的 `QISRAudioWrite()` 对应 `QISR` 实例的 `AudioWrite()` 方法. 

### 参数

1. 参数名从驼峰式命名改为下划线连接

2. 为了简化调用, 删除 `sessionID` 参数, 统一改为从 `self.sessionID` 获取 (需要先调用一次对应的 `SessionBegin()` 方法). 

3. 为了简化调用, 删除所有表示 "数据长度" 的参数, 改为在函数体中通过传入的数据计算得出

4. 为了简化调用, 删除所有 C 函数中传入值固定为 `NULL` 的参数

5. 删除了所有的引用传入的变量, 改为在返回值中返回结果

6. 所有的 `params` 参数都接受字典或字符串两种形式的输入, 默认值以字典形式在对应类的 `__init__()` 中初始化

### 返回值

1. 如果 C 函数只返回表示 "是否执行成功" 的状态码, 则对应的 python 方法会在函数体中对这个返回值做判断, 如果不等于 `MSP_SUCCESS` 会直接抛出 `RuntimeError` 和对应的错误码, 且不再返回该状态码. 因此这类函数对应的 python 方法没有返回值. 例如 `MSPLogin()` 对应的 `MSP_CMN` 类的 `Login()` 方法.

2. 引用传递的参数按照在文档中出现的顺序返回. (同 1., 如果某个引用参数是表示执行成功与否的状态码, 则会在函数体中进行处理而不再返回)

3. 如果 C 函数的返回值是指针, 会解码为 python 类型再返回.

4. 字符串/json/字典类型的返回值会解码为 python 字符串并返回. (除了返回 `sessionID` 的方法, 返回的是 `bytes` 类型的字符串)

5. 返回音频的方法会返回音频字节流, 可以通过 `Recorder` 类的 `play_buffer()` 方法播放.

### 已知问题

1. 所有的 `GetParam()` 方法暂时无法正常调用, 返回的 error code 为 -1, 原因未知.

2. 偶尔会出现 `QISR` 的 `AudioWrite()` 方法在最后一块音频输入以后返回的引用参数 `rsltStatus` 不为 `MSP_REC_STATUS_SUCCESS` 的情况.

## 常见问题

1. 如何运行官方的 sample

以 tts_online_sample 为例：

```bash
cd sdk/samples/tts_online_sample
source 64bit_make.sh
# 注意是用 source 而不是用 sh 执行，这一步生成的可执行文件在 sdk/bin 文件夹
cd ../../bin
./tts_online_sample
```

2. 报错 `error while loading shared libraries: libmsc.so: cannot open shared object file: No such file or directory`

实测在 Ubuntu 16.04 环境下需要把 `libmsc.so` 复制到 `/usr/bin`（取决于环境，也有可能是 `/usr/local/bin`）

```bash
cd sdk/libs/x64         # x64/x86 取决于硬件，自行修改
sudo cp lib* /usr/bin   # 为了保险起见全部复制，应该也可以只复制 libmsc.so 
# sudo cp lib* /usr/local/bin
```

3. 如果出现 ALSA 7963 错误：

https://retro64xyz.gitlab.io/how-to/2017/05/26/how-to-fix-audacity-underrun/

4. 是否兼容 Windows 平台

理论上可以, 参照 [ctypes 文档](https://docs.python.org/zh-cn/3.6/library/ctypes.html#loading-dynamic-link-libraries) 修改 `MSP_CMN.py` 中 `dll` 的载入方式为 `WinDLL` . 另外, 可能需要将所有的 `CFUNCTYPE` 装饰器修改为 `WINFUNCTYPE`. 请自行测试.

5. 音效文件 

[wakeup.wav](https://www.ear0.com/sound/show/soundid-13122)

[sleep.wav](https://www.ear0.com/sound/show/soundid-10977)