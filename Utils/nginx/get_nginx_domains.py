#!/usr/bin/env python

import argparse
import pprint
import re
import sys

sys.path.append('.')
from nginx_apis import NginxKeyVals


class CliArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-a", "--ip_addrs", default=None, type=str, nargs='+',
                                 help="IP Addresses of target Nginx devices")
        self.parser.add_argument("-p", "--port", default=DEFAULT_PORT, type=int,
                                 help=f"Nginx API Server Port. DEFAULT: {DEFAULT_PORT}")
        self.args = self.parser.parse_args()


def build_target_name(fqdn: str, delimiter: str = '.') -> str:
    """
    Build the version string: {numerical_build_number}_{env}

    :param fqdn: Fully qualified domain name to parse and build ini target file section name version
    :param delimiter: delimiter in FDQN. Default = '.'

    :return: (str) Target INI section file name {version|name}_{env}
    """
    parts = fqdn.split(delimiter)
    version, env = (parts[0], parts[1])
    numerical_version = convert_version_to_number(version)
    return f"{numerical_version}_{env}"


def convert_version_to_number(version_number: str) -> str:
    """
    Converts the version from text to a numerical convention.

    Given twentyone --> 20.1, thirtythreeseven --> 33.7, qa_test --> qa_test

    :param version_number: text representation of build string

    :return: string: major.minor numerical representation.

    """
    minors = {'one': 1, 'two': 2, 'three': 3, 'four': 4,
              'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
              'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12}
    majors = {'nineteen': 19, 'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60}

    version_number = version_number.lower()

    # Determine the year value.
    for major_string, major_value in majors.items():
        if not version_number.startswith(major_string):
            continue

        version_number = re.sub(major_string, '', version_number, 1)

        # Determine if the next value is part of the major version (twentyone) or the minor version (one)
        for minor_string, minor_value in minors.items():
            if not version_number.startswith(minor_string):
                continue

            # Next match identified.
            next_version_segment = re.sub(minor_string, '', version_number, 1)
            current_minor_value = minor_value

            # See if there is any more version string to process:
            #     If not, the previous number is the minor version.
            #     If so, the previous number is part of the major version, so add that to the major version value,
            #        and determine the minor version.
            if next_version_segment != '':
                major_value += minor_value
                for minor_string, minor_value in minors.items():
                    if not next_version_segment.startswith(minor_string):
                        continue
                    current_minor_value = minor_value

            return f"{major_value}.{current_minor_value}"

    # If you get here, there was no version number to be converted, so return original value.
    return version_number


if __name__ == '__main__':
    DEFAULT_IPS = ['10.9.20.10']
    DEFAULT_PORT = 8989
    ZONE_NAME = 'los'
    (user, pswd) = ('*' * 8, '*' * 8)

    cli = CliArgs()

    api_base_url = f'http://{{ip_address}}:{cli.args.port}/api/6'
    ip_addresses = DEFAULT_IPS if cli.args.ip_addrs is None else cli.args.ip_addrs

    for ip in ip_addresses:
        nginx = NginxKeyVals(username=user, password=pswd, base_url=api_base_url.format(ip_address=ip))
        fqdns = nginx.get_stream_keyvals(zone_name=ZONE_NAME)
        for target, port in sorted(fqdns.items(), key=lambda x: int(x[1])):
            print(f"{build_target_name(target)}:{port} <== {target}")
