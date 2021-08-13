import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-bg", "--build_grammar", help="Build grammar before recognization for local ISR.", action="store_true")
parser.add_argument("-lg", "--local_grammar", type=str, default="coffeebar", help="local grammar")
parser.add_argument("--sr_type", type=str, default="asr", help="asr 离线命令词识别, isr 在线识别")

args = parser.parse_args()