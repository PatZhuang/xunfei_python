## 项目简介

本项目是 x86/x64 Linux 平台的讯飞 SDK 的 python 实现

可用功能: 语音唤醒, 离线命令词识别, 离线/在线语音合成, AIUI 平台交互 (前三者基于原生 SDK, AIUI 基于 webapi)

## 准备工作

1. 讯飞 SDK

> `AIUI_webapi.py` 不使用 SDK, 只需要申请一个 WebAPI 类型的应用, 这一步可以跳过.

本工程仅支持 x64 Linux 平台. 所需的 SDK 有: 离线命令词识别, 离线语音合成(普通版/高品质版), 语音唤醒, 在线语音合成(流式版), 语音听写(流式版), AIUI 平台

> 在讯飞控制台生成 APP 时必须选择平台为 Linux 生成 SDK.

解压 SDK 到 `<xunfei_SDK>` 目录, 然后将其中的 `libs` 和 `msc` 文件夹软链接到本工程根目录:

```bash

# 软链接
ln -s <xunfei_SDK>/libs .
ln -s <xunfei_SDK>/msc .

# 动态库复制到系统路径
# 如果是 x86 自行替换路径
sudo cp <xunfei_SDK>/libs/x64/*.so /usr/bin
sudo cp <xunfei_SDK>/libs/x64/*.so /usr/local/bin
```

2. Python 依赖

本工程基于 python 3.9.6, 理论上 python 版本 >= 3.6 都能运行. 所需的依赖在 `requirements.txt` 中

```bash
pip install -r requirements.txt
```

> 如果非要使用 python 3.5 及以下, 请把代码中所有 `from rich import print` 删除. 其他库是否兼容请自行测试.

3. APPID

如果要使用 Linux SDK, 需要在讯飞控制台注册一个类型为 Linux 的应用.

`MSP_CMN.py` 中的 `APP_ID` 修改为自己的 `APP_ID` (Linux 平台)

如果要使用 webapi, 需要在讯飞控制台注册一个类型为 WebAPI 的应用.

自行创建一个 `AIUI_CMN.py 文件`, 内容为:

```python
WEB_APPID = "xxx"   # WebAPI 平台
API_KEY = "xxx"     # WebAPI 平台
AUTH_ID = "xxx"
```

根据自己的应用填写对应内容. AUTH_ID 是一个任意的 MD5 字符串, 可以随意设置. 比如用 python 生成:

```python
import hashlib

md5 = hashlib.md5()
md5.update("anything you want to hash")
AUTH_ID = md5.hexdigest()
```

## 文件对应功能

注意, 并不是所有 SDK 文档中提到的函数都做了对应 python 实现. 这里只实现了本项目所需的函数.

具体文档参考: [MSC_API 文档](https://www.xfyun.cn/doc/mscapi/Windows&Linux/wlapi.html)

### MSP_CMN.py

对应讯飞 SDK 中的 `msp_cmn.h`, 实现为一个同名的类 `MSP_CMN`. 使用时需要构造一个 `MSP_CMN` 对象.

其中函数名和参数类型与官方文档尽可能对应. 例如 C 函数中的 `MSPLogin` 对应 `MSP_CMN` 对象的 `Login` 方法.

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

其中函数名和参数类型与官方文档尽可能对应. 例如 C 函数中的 `QIVWSessionbegin()` 对应 `QIVW` 对象的 `Sessionbegin()` 方法.

### 离线命令词 QISR.py

对应讯飞 SDK 中的 `qisr.py`, 实现为一个同名的类 `QISR`. 使用时需要构造一个 `QISR` 对象.

请参考 [语法开发指南](http://bbs.xfyun.cn/thread/7595) 构造本地语法文件 `xxx.bnf` 并替换 `QISR.py` 中的 `GRM_FILE` 变量

第一次运行离线命令词识别前需要使用 `--build_grammar` 或 `-bg` 参数构建本地语法网络, 之后运行时可以使用 `--local_grammar xxx` 或 `-lg xxx` 参数加载本地语法. 具体查看 `params.py`.

其中函数名和参数类型与官方文档尽可能对应. 例如 C 函数中的 `QISRAudioWrite()` 对应 `QISR` 对象的 `AudioWrite()` 方法.

### 语音合成 QTTS.py

对应讯飞 SDK 中的 `qtts.py`, 实现为一个同名的类 `QTTS`. 使用时需要构造一个 `QTTS` 对象.

其中函数名和参数类型与官方文档尽可能对应. 例如 C 函数中的  `QTTSTextPut()` 对应 `QTTS` 对象的 `TextPut()` 方法.

### AIUI_webapi.py

`AIUI_webapi.py` 是 AIUI 的 webapi 接口的实现. 具体请参考: [WebAPI 接口文档](https://aiui.xfyun.cn/doc/aiui/develop/more_doc/webapi/summary.html)

### 音频接口

`Recorder.py` 是基于 `sounuddevice` 的音频接口实现. 功能包含: 播放本地音频, 播放内存中的数据, 音频录制, 端点检测 (使用 `webrtcvad`)

### 注意事项

1. 上述所有 `.py` 文件都可以直接 `python xxx.py` 直接运行, 请自行阅读代码. 

2. SDK 相关文件均根据 Linux SDK 文档中的 "API 调用流程" 所示流程图执行业务逻辑, 例如 [语音唤醒](https://www.xfyun.cn/doc/asr/awaken/Linux-SDK.html#_2、sdk集成指南). 也可以参阅 SDK 自带的 C 程序示例.

3. 请不要直接运行 `main.py`, 请根据自己的业务需求进行修改.

## 问题记录

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

4. 如何使用原生 SDK 做在线语音识别

还没写, 但是 AIUI 的 WebAPI 可以做到同样的功能. 注意 AIUI WebAPI 不支持流式识别, 需要在本地构造完整的音频片段并一次性上传. 如果是在线录制, 可以使用 `Recorder` 类中的 `get_record_audio_with_vad` 自动判断录音结束并截断.

5. 是否兼容 Windows 平台

理论上可以, 参照 [ctypes 文档](https://docs.python.org/zh-cn/3.6/library/ctypes.html#loading-dynamic-link-libraries) 修改 `MSP_CMN.py` 中 `dll` 的载入方式为 `WinDLL` . 另外, 可能需要将所有的 `CFUNCTYPE` 装饰器修改为 `WINFUNCTYPE`. 请自行测试.