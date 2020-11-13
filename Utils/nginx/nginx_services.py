#!/usr/bin/env python3
import argparse
import pprint
import sys

sys.path.append('.')
from nginx_apis import NginxServerInfo


class CliArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-a", "--ip_addrs", default=None, type=str, nargs='+',
                                 help="IP Addresses of target Nginx devices")
        self.parser.add_argument("-p", "--port", default=DEFAULT_PORT, type=int,
                                 help=f"Nginx API Server Port. DEFAULT: {DEFAULT_PORT}")
        self.parser.add_argument("-s", "--services", default=None, type=str, nargs='+',
                                 help="Name of service(s)",)
        self.parser.add_argument("-i", "--server_index",  default=None, type=int,
                                 help="Server index number. "
                                      "NOTE: If not specified, all registered indices will be used. "
                                      "If multiple services are specified, this argument is ignored.")
        self.parser.add_argument("-f", "--fields", default=None, type=str, nargs='+',
                                 help="Fields to set (name:value).")
        self.args = self.parser.parse_args()
        self._check_conditions()

    def _check_conditions(self) -> None:
        """
        Print out a warning if certain conditions/combinations of arguments are specified.

        :return: None

        """
        if self.args.server_index is not None:
            if self.args.services is None or (self.args.services is not None and len(self.args.services) > 1):
                print(f"\n***NOTE***: Multiple services have been specified, ignoring the specified index value: "
                      f"'{self.args.server_index}'.\n")

        if self.args.fields is not None:
            diff = set([x.split(':')[0] for x in self.args.fields]) - set(NginxServerInfo.OPTIONS)
            if diff:
                print(f"***ERROR***:\n\tUnrecognized server field options: {list(diff)}. "
                      f"Ignoring unrecognized option(s).")
                self.args.fields = [arg for arg in self.args.fields if arg.split(':')[0] not in diff]


if __name__ == '__main__':
    DEFAULT_IPS = ['10.9.20.10']
    DEFAULT_PORT = 8989
    DEFAULT_FIELDS = [NginxServerInfo.SERVER, NginxServerInfo.DOWN]

    (user, pswd) = ('********', '*********')

    # Parse CLI args
    cli = CliArgs()
    api_base_url = f'http://{{ip_address}}:{cli.args.port}/api/6'
    nginx_ips = cli.args.ip_addrs if cli.args.ip_addrs is not None else DEFAULT_IPS
    services = cli.args.services
    index = cli.args.server_index

    attribute_dict = None
    target_fields = None
    if cli.args.fields is not None:
        attribute_dict = dict([(x.split(":")[0], x.split(":")[1]) for x in cli.args.fields])
        target_fields = list(attribute_dict.keys())

    # For each Nginx API IP that needs to be queried...
    for ip in nginx_ips:

        # Instantiate API interaction class (store credentials, base_url, etc.)
        nginx_apis = NginxServerInfo(
            username=user, password=pswd, base_url=api_base_url.format(ip_address=ip))

        if services is None:
            services = nginx_apis.get_list_of_services()

        # Report server status prior to change
        server_status = nginx_apis.get_server_status_info(
            service=services, server_index=index, fields=target_fields)
        print(f"SERVER STATUSES:\n{pprint.pformat(server_status)}\n")

        # Make requested changes
        if attribute_dict:
            for service in services:
                nginx_apis.set_server_attributes(
                    service=service, server_id=index, attribute_dict=attribute_dict)
                print()

        # Report server status after change
        server_status = nginx_apis.get_server_status_info(
            service=services, server_index=index, fields=target_fields)
        print(f"\nSERVER STATUSES:\n{pprint.pformat(server_status)}")
