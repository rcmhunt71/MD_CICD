import sys

import winrm

# Implemented for python 2.7+ < python 3.x+

server = "PCLDEVWEB05.DEVELOPMENT.PCLENDER.LOCAL"
transport = "kerberos"
cert_validation = 'ignore'

user = sys.argv[1]
pswd = sys.argv[2]


print "Using: {user}:{pswd} to connect to: {svr}".format(user=user, pswd=pswd, svr=server)

s = winrm.Session(
    server,
    transport=transport,
    auth=(user, pswd),
    server_cert_validation=cert_validation)

print "Session: {0}".format(s)

r = s.run_cmd('ipconfig', ['/all'])

print "Response: {resp}".format(resp=r)
