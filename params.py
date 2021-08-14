import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-bg", "--build_grammar", help="Build grammar before recognization for local ISR.", action="store_true")
parser.add_argument("-lg", "--local_grammar", type=str, default="coffeebar", help="local grammar")
parser.add_argument("--sr_type", type=str, default="asr", help="asr 离线命令词识别, isr 在线识别")
parser.add_argument("--tts_text", type=str, default="这是一条示例合成文本", help="语音合成的文本")

args = parser.parse_args()