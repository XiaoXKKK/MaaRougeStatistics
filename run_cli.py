from python.relic_counter import RelicRecognition

import sys
import os
# if not os.path.exists("run_cli.py"):
#     os.environ["MAAFW_BINARY_PATH"] = os.getcwd()

from maa.toolkit import Toolkit

def main():
    Toolkit.pi_register_custom_action("RelicRecognition", RelicRecognition())

    directly = "-d" in sys.argv
    Toolkit.pi_run_cli("./", "./", directly)

if __name__ == "__main__":
    main()