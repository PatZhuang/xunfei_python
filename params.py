import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-bg", "--build_grammar", help="Build grammar before recognization for local ISR.", action="store_true", default=False)
parser.add_argument("-lg", "--local_grammar", type=str, default="coffeebar", help="local grammar")
parser.add_argument("--sr_type", type=str, default="asr", help="asr 离线命令词识别, isr 在线识别")
parser.add_argument("--tts_text", '-tts', type=str, default="这是一条示例合成文本", help="语音合成的文本")
parser.add_argument("--output_audio_file", '-o', type=str, default=None, help="tts 合成音频保存的文件名")

args = parser.parse_args()