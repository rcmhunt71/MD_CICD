#!/usr/bin/env python

import argparse
import pprint
import sys

sys.path.append('.')
from nginx_configured_server_info import NginxServerInfo

class CliArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-a", "--ip_addrs", default=None, type=str, nargs='+',
                                 help="IP Addresses of target Nginx devices")
        self.parser.add_argument("-p", "--port", default=DEFAULT_PORT, type=int,
                                 help=f"Nginx API Server Port. DEFAULT: {DEFAULT_PORT}")
        self.args = self.parser.parse_args()


if __name__ == '__main__':
    DEFAULT_IPS = ['10.9.20.10']
    DEFAULT_PORT = 8989
    (user, pswd) = ('*' * 8, '*' * 8)

    cli = CliArgs()

    api_base_url = f'http://{{ip_address}}:{cli.args.port}/api/6'
    ip_addresses = DEFAULT_IPS if cli.args.ip_addrs is None else cli.args.ip_addrs

    services = []
    for ip in ip_addresses:
        nginx = NginxServerInfo(username=user, password=pswd, base_url=api_base_url.format(ip_address=ip))
        services.extend(nginx.get_list_of_services())

    pprint.pprint(services)
