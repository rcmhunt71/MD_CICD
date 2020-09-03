#!/usr/bin/env python
import argparse
import pprint
import requests
from requests.auth import HTTPBasicAuth
import typing


DEFAULT_IPS = ['10.9.20.10']
DEFAULT_PORT = 8989


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
        self.args = self.parser.parse_args()
        self._check_conditions()

    def _check_conditions(self) -> None:
        """
        Print out a warning if certain conditions/combinations of arguments are specified.

        :return: None

        """
        if self.args.server_index is not None:
            if self.args.service is None or (self.args.service is not None and len(self.args.service) > 1):
                print(f"\n***NOTE***: Multiple services have been specified, ignoring the specified index value: "
                      f"'{self.args.server_index}'.\n")


class NginxServerInfo:
    """
    Provides basic functionality to interact with Nginx APIs.
    - /stream/upstreams/
    - /stream/upstreams/{streamUpstreamName}/servers/

    """

    # JSON Response Keywords
    DOWN = 'down'
    ID = 'id'
    SERVER = 'server'

    def __init__(self, username: str, password: str, base_url: str) -> None:
        """
        Nginx Server Info Constructor

        :param username: Name to use when authenticate against the API
        :param password: Password to use when authenticate against the API
        :param base_url: Primary API URL

        """
        self.username = username
        self.password = password
        self.base_url = base_url
        self.auth = HTTPBasicAuth(self.username, self.password)

    def get_upstream_info(self) -> dict:
        """
        Gets basic upstream info: name of services, servers per services, and metadata describing each server

        :return: JSON formatted API response

        """
        url_resource = "/stream/upstreams/"

        url = self.base_url + url_resource
        resp = requests.get(url, auth=self.auth)

        if int(resp.status_code) == 200:
            data = resp.json()
        else:
            data = {}
            print(f"\tERROR: Unexpected response from {url}: STATUS CODE: {resp.status_code}")

        return data

    def get_list_of_services(self) -> typing.List[str]:
        """
        Returns list of configured services

        :return: List of configured services
        """
        return list(self.get_upstream_info().keys())

    def get_server_status_info(
            self, service: typing.Optional[list] = None, index: typing.Optional[int] = None,
            fields: typing.Optional[list] = None) -> dict:
        """
        Get status information for each server, based on server id.

        :param service: Name of specific server. If not specified, get a list of the services.
        :param index: For a single service, specify the server index. If multiple servers, all indexes will be returned.
        :param fields: List of server fields to retrieve; if not specified, defaults to SERVER IP and DOWN status.

        :return: Dictionary of server information: [server][server_id][ [field1: attribute1]. [field2, attribute2] ]

        """

        url_resource = '/stream/upstreams/{streamUpstreamName}/servers/'

        fields = fields or [self.SERVER, self.DOWN]
        service = service or self.get_list_of_services()

        server_info = dict()
        for server in service:

            # Get upstream server info
            url = self.base_url + url_resource.format(streamUpstreamName=server)
            resp = requests.get(url, auth=self.auth)
            if resp.status_code != 200:
                print(f"\tERROR: Unexpected response from {url}: STATUS CODE: {resp.status_code}")
                continue

            # Convert to json and parse out desired fields
            data = resp.json()
            server_info[server] = dict()
            for idx, server_dict in enumerate(data):
                if len(service) == 1 and index is not None and idx != index:
                    continue
                server_info[server][server_dict[self.ID]] = dict([(key, server_dict[key]) for key in fields])

        return server_info

    def set_server_attributes(self, service: str, server_id: int, attribute_dict: dict) -> bool:
        """
        Set specific server attributes.

        :param service: Name of specific service
        :param server_id: Index of specific upstream server
        :param attribute_dict: Dictionary of attributes (field1: value1, field2: value2)

        :return: True = value(s) set and verified,
                 False = not all values were set successfully.
                 See console output for error details.
        """
        result = self._set_server_attributes(service=service, server_id=server_id, attribute_dict=attribute_dict)
        return result and self._verify_server_attributes(
            service=service, server_id=server_id, attribute_dict=attribute_dict)

    def _verify_server_attributes(self, service: str, server_id: int, attribute_dict: dict) -> bool:
        """
        Verify server attributes match expected values

        :param service: Name of service
        :param server_id: Index of specific server in service
        :param attribute_dict: Dictionary of attributes and expected values.

        :return: True = server attributes match expected values

        """
        try:
            server_info = self.get_server_status_info(fields=list(attribute_dict.keys()))[server_id]
        except KeyError as err:
            print(f"\tERROR: Unknown server id ({server_id}) for {service}")
            status = False
        else:
            status = True
            for key, value in attribute_dict.items():
                status = status and server_info[key] == value
        return status

    def _set_server_attributes(self, service: str, server_id: int, attribute_dict: dict) -> bool:
        """
        Set the server attributes to specified values

        :param service: Name of service
        :param server_id: Index of specific server in service
        :param attribute_dict: Dictionary of attributes and corresponding desired values.

        :return: True: values set (but not validated),
                 False: Unable to set values
                 See console output for error details.
        """
        url_resource = '/stream/upstreams/{{streamUpStreamName}/servers/{streamUpstreamServerId}'

        url = self.base_url + url_resource.format(streamUpStreamName=service, streamUpstreamServerIddd=server_id)

        resp = requests.patch(url, auth=self.auth, payload=attribute_dict)
        status = resp.status_code == 200
        if not status:
            print(f"\tERROR: Unexpected response from {url}: STATUS CODE: {resp.status_code}")

        return status


if __name__ == '__main__':
    (user, pswd) = ('*****', '******')

    # Parse CLI args
    cli = CliArgs()
    api_base_url = f'http://{{ip_address}}:{cli.args.port}/api/6'
    nginx_ips = cli.args.ip_addrs if cli.args.ip_addrs is not None else DEFAULT_IPS
    service = cli.args.service
    index = cli.args.server_index

    # For each Nginx API IP that needs to be queried...
    for ip in nginx_ips:

        # Instantiate API interaction class (store credentials, base_url, etc.)
        nginx_apis = NginxServerInfo(
            username=user, password=pswd, base_url=api_base_url.format(ip_address=ip))

        # Get the server status (and show the results)
        server_status = nginx_apis.get_server_status_info(service=service, index=index)
        pprint.pprint(server_status)
