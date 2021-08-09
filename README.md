## 问题记录

1. 如何运行 sample

以 tts_online_sample 为例：

```bash
cd sdk/samples/tts_online_sample
source 64bit_make.sh
# 注意是用 source 而不是用 sh 执行，这一步生成的可执行文件在 sdk/bin 文件夹
cd ../../bin/tts_online_sample
```

2. 报错 `error while loading shared libraries: libmsc.so: cannot open shared object file: No such file or directory`

实测在 Ubuntu 16.04 环境下需要把 `libmsc.so` 复制到 `/usr/bin`（取决于环境，也有可能是 `/usr/local/bin`）

```bash
cd sdk/libs/x64         # x64/x86 取决于硬件，自行修改
sudo cp lib* /usr/bin   # 为了保险起见全部复制，应该也可以只复制 libmsc.so 
```

3. 如果出现 ALSA 7963 错误：

https://retro64xyz.gitlab.io/how-to/2017/05/26/how-to-fix-audacity-underrun/