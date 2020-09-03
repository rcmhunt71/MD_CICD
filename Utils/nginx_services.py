#!/usr/bin/env python
import pprint
import requests
from requests.auth import HTTPBasicAuth
import typing


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
        RESOURCE = "/stream/upstreams/"

        url = self.base_url + RESOURCE
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
            self, servers: typing.Optional[list] = None, fields: typing.Optional[list] = None) -> dict:
        """
        Get status information for each server, based on server id.

        :param servers: Name of specific server. If not specified, get a list of the services.
        :param fields: List of server fields to retrieve; if not specified, defaults to SERVER IP and DOWN status.

        :return: Dictionary of server information: [server][server_id][ [field1: attribute1]. [field2, attribute2] ]

        """

        RESOURCE = '/stream/upstreams/{streamUpstreamName}/servers/'

        fields = fields or [self.SERVER, self.DOWN]
        servers = servers or self.get_list_of_services()

        server_info = dict()
        for server in servers:

            # Get upstream server info
            url = self.base_url + RESOURCE.format(streamUpstreamName=server)
            resp = requests.get(url, auth=self.auth)
            if resp.status_code != 200:
                print(f"\tERROR: Unexpected response from {url}: STATUS CODE: {resp.status_code}")
                continue

            # Convert to json and parse out desired fields
            data = resp.json()
            server_info[server] = dict()
            for server_dict in data:
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
        RESOURCE = '/stream/upstreams/{{streamUpStreamName}/servers/{streamUpstreamServerId}'

        url = self.base_url + RESOURCE.format(streamUpStreamName=service, streamUpstreamServerIddd=server_id)

        resp = requests.patch(url, auth=self.auth, payload=attribute_dict)
        status = resp.status_code == 200
        if not status:
            print(f"\tERROR: Unexpected response from {url}: STATUS CODE: {resp.status_code}")

        return status


if __name__ == '__main__':
    (user, pswd) = ('********', '********')

    api_base_url = 'http://{ip_address}:8989/api/6'
    nginx_ips = ['10.9.20.10']
    servers = ['los_adam']

    # For each Nginx API IP that needs to be queried...
    for ip in nginx_ips:

        # Instantiate API interaction class (store credentials, base_url, etc.)
        nginx_server_apis = NginxServerInfo(
            username=user, password=pswd, base_url=api_base_url.format(ip_address=ip))

        # Get the server status (and show the results)
        server_status = nginx_server_apis.get_server_status_info(servers=servers)
        pprint.pprint(server_status)
