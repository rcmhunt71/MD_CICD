
#/!usr/bin/env python
import argparse
import sys


number_to_text_definitions = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen",
    20: "twenty",
    30: "thirty",
    40: "forty",
    50: "fifty",
    60: "sixty",
    70: "seventy",
    80: "eighty",
    90: "ninety",
    100: "hundred",
}


class CLIOptions:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("build_number", help="Build Number")
        self.parser.add_argument("-d", "--delimiter", help="Build Number Delimiter", default='.')
        self.args = self.parser.parse_args()


class ConvertToText:

    @staticmethod
    def convert_to_text(number: int) -> str:
        min_value, max_value = 0, 100
        if min_value <= number < max_value:
            if min_value <= number <= 20 or number % 10 == 0:
                conversion = number_to_text_definitions[number]
            else:
                conversion = (number_to_text_definitions[int(str(number)[-2]) * 10] +
                              number_to_text_definitions[int(str(number)[-1])])
        else:
            conversion = f"convert_to_text only supports a range of integers: [{min_value}, {max_value}]"

        return conversion

    @staticmethod
    def build_number(build_num: str, build_delimiter: str = '.') -> str:
        return "".join([f"{ConvertToText.convert_to_text(int(vers))}".capitalize() for vers
                        in build_num.split(build_delimiter)])


if __name__ == '__main__':
    args = CLIOptions().args
    print(ConvertToText.build_number(args.build_number, args.delimiter))

