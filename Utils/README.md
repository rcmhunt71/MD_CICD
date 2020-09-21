#THE PURPOSE OF UTILITIES

## Nginx 
### Libraries ###
_nginx_apis.py_
* This library contains various Nginx clients for interacting with the Nginx devices.
  * Class: _NginxKeyVals_
    * Get the Nginx KeyVal data.
  * Class: _NginxServerInfo_
    * Get  configuration information such as registered services, servers, server attributes.
    * Set server attributes, verify attributes match expectations.

### Utilities ###
_get_nginx_domains.py_ 
- Using the Nginx APIs, the utility pulls the values + ports that are registered in the Nginx's KeyVal mapping store, and creates the corresponding FQDN.
- **Input**:  (add -h to the command line execution to see the parameter list)
   * REQUIRED Arguments: 
     * **None**
   * OPTIONAL Arguments:
     * **``-a IP_ADDRS [IP_ADDRS ...]`` or ``--ip_addrs IP_ADDRS [IP_ADDRS ...]``**  --> IP Addresses of target Nginx devices
     * **``-p PORT`` or ``--port PORT``**  --> Nginx API Server Port. Default=8989
     * **``-y YAML`` or ``--yaml YAML``**  --> Name of yaml file to write FQDN (for use in configuring through JJB)
     
- **Output**:
  * **Format**: ``[subdomain name]:[port]`` <== ``[FQDN]``
  * **Example**:
    * ``20.2_dev:20020 <== twentytwo.dev.mortgagedirector.com``
    * ``20.3_dev:20030 <== twentythree.dev.mortgagedirector.com``
    * ``20.5_dev:20050 <== twentyfive.dev.mortgagedirector.com``
    
  ----------------------------------
  _nginx_services.py_
  
  * This utility allows the setting of various server attributed for the defined Nginx services. The utility will display the states of the requested attributes, set AND verify the updated attributes, and then query & display the current settings.
  
  - **Input**: (add -h to the command line execution to see the parameter list)
    * REQUIRED Arguments:
      * **None**
    * OPTIONAL Arguments:
      * ``-a IP_ADDRS [IP_ADDRS ...]`` or  ``--ip_addrs IP_ADDRS [IP_ADDRS ...]`` --> IP Addresses of target Nginx devices
      * ``-p PORT`` or ``--port PORT`` --> Nginx API Server Port. DEFAULT: 8989
      * ``-s SERVICES [SERVICES ...]`` or ``--services SERVICES [SERVICES ...]`` --> Name of service(s)
      * ``-i SERVER_INDEX`` or ``--server_index SERVER_INDEX`` --> Server index number. NOTE: If not specified, all registered indices will be used. If multiple services are specified, this argument is ignored.
      * ``-f FIELDS [FIELDS ...]`` or ``--fields FIELDS [FIELDS ...]`` --> Fields to set (name:value).
      
  - **OUTPUT**:
    * List of services and the current settings for the provided attributes.
    * Report of the settings changes and the results of validating the change.
    * List of services and the current settings for the provided attributes.
