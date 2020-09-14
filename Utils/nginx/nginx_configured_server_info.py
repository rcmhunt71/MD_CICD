import typing

import requests
from requests.auth import HTTPBasicAuth


class NginxServerInfo:
    """
    Provides basic functionality to interact with Nginx APIs.
    - /stream/upstreams/
    - /stream/upstreams/{streamUpstreamName}/servers/

    """

    # JSON Response Keywords
    BACKUP = 'backup'
    DOWN = 'down'
    FAIL_TIMEOUT = 'fail_timeout'
    ID = 'id'
    MAX_CONNS = 'max_conns'
    MAX_FAILS = 'max_fails'
    PEERS = 'peers'
    SERVER = 'server'
    WEIGHT = 'weight'
    OPTIONS = [BACKUP, DOWN, FAIL_TIMEOUT, ID, MAX_CONNS, MAX_FAILS, SERVER, WEIGHT]

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
            print(f"\tERROR: Unexpected response from GET {url}: STATUS CODE: {resp.status_code}")

        return data

    def get_list_of_services(self) -> typing.List[str]:
        """
        Returns list of configured services

        :return: List of configured services
        """
        return list(self.get_upstream_info().keys())

    def get_number_of_servers(self, service: str) -> int:
        """
        Determine the number of servers associated with a given service.

        :param service: Name of the service

        :return: (int) Number of servers
        """
        return len(self.get_upstream_info()[service][NginxServerInfo.PEERS])

    def get_server_status_info(
            self, service: typing.Optional[list] = None, server_index: typing.Optional[int] = None,
            fields: typing.Optional[list] = None) -> dict:
        """
        Get status information for each server, based on server id.

        :param service: Name of specific server. If not specified, get a list of the services.
        :param server_index: For a single service, specify the server index. If multiple servers, all indexes will
                   be returned.
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
                print(f"\tERROR: Unexpected response from GET {url}: STATUS CODE: {resp.status_code}")
                continue

            # Convert to json and parse out desired fields
            data = resp.json()
            server_info[server] = dict()
            for idx, server_dict in enumerate(data):
                if len(service) == 1 and server_index is not None and idx != server_index:
                    continue
                server_info[server][server_dict[self.ID]] = dict([(key, server_dict[key]) for key in fields])

        return server_info

    def set_server_attributes(self, service: str, attribute_dict: dict, server_id: typing.Optional[int] = None) -> bool:
        """
        Set specific server attributes.

        :param service: Name of specific service
        :param attribute_dict: Dictionary of attributes (field1: value1, field2: value2)
        :param server_id: Index of specific upstream server

        :return: True = value(s) set and verified,
                 False = not all values were set successfully.
                 See console output for error details.

        """
        if server_id is None:
            number_of_ids = self.get_number_of_servers(service)
            server_ids = range(self.get_number_of_servers(service))

        else:
            number_of_ids = 1
            server_ids = [server_id]

        print(f"Service: {service} has {number_of_ids} servers:")

        result = True
        for server_id in server_ids:
            result = result and self._set_server_attributes(
                service=service, server_id=server_id, attribute_dict=attribute_dict)
            result = result and self._verify_server_attributes(
                service=service, server_id=server_id, attribute_dict=attribute_dict)
        return result

    def _verify_server_attributes(self, service: str, server_id: int, attribute_dict: dict) -> bool:
        """
        Verify server attributes match expected values

        :param service: Name of service
        :param server_id: Index of specific server in service
        :param attribute_dict: Dictionary of attributes and expected values.

        :return: True = server attributes match expected values

        """
        try:
            server_info = self.get_server_status_info(fields=list(attribute_dict.keys()))[service][server_id]
        except KeyError:
            print(f"\tERROR: Unknown server id ({server_id}) for {service}")
            status = False
        else:
            status = True
            for key, value in attribute_dict.items():
                result = str(server_info[key]).lower() == str(value).lower()
                status = status and result
                print(f"\t- Verifying service '{service}' --> server #{server_id} property '{key}' "
                      f"was set to '{value}': {'PASS' if result else 'FAIL'} ")
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
        url_resource = '/stream/upstreams/{streamUpStreamName}/servers/{streamUpstreamServerId}'

        url = self.base_url + url_resource.format(streamUpStreamName=service, streamUpstreamServerId=server_id)
        for key, value in attribute_dict.items():
            print(f"\t- Setting service '{service}' --> server #{server_id} property '{key}' was set to '{value}':   ",
                  end='')

        resp = requests.patch(url, auth=self.auth, json=attribute_dict)
        status = resp.status_code == 200
        if not status:
            print("ERROR")
            print(f"\tERROR: Unexpected response from PATCH {url}: STATUS CODE: {resp.status_code}")
        else:
            print("DONE")

        return status
