#!/usr/bin/env python3


import argparse

class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("build_number", help="Build Version number: X.Y.Z.a")
        self.args = self.parser.parse_args()

if __name__ == "__main__":
    build_nums = CLI().args.build_number.split('.')
    port = f"{build_nums[0]:0>2}{build_nums[1]:0>2}"
    port += build_nums[2] if len(build_nums) > 2 else "0"
    print(port)
