import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-bg", "--build_grammar", help="Build grammar before recognization for local ISR.", action="store_true")
parser.add_argument("-lg", "--local_grammar", type=str, help="local grammar")

args = parser.parse_args()