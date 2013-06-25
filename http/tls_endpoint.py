import socket
import ssl
import time
import os
from random import randint
from OpenSSL import crypto,SSL
from M2Crypto import X509
from cert_generate import mk_casigned_cert
from cert_generate import mk_temporary_cert

def setup_ca():
    if(not os.path.exists(os.getcwd()+"/certs/ca")):
        os.makedirs(os.getcwd()+"/certs/ca/")
    
    cacert,cert,key = mk_casigned_cert()
    with open(os.getcwd()+"/certs/ca/cacert.crt","w") as f:
        f.write(cacert.as_pem())
    with open(os.getcwd()+"/certs/ca/cert.crt","w") as f:
        f.write(cert.as_pem())
        f.write(key.as_pem(None))

    # check is valid
    cac = X509.load_cert(os.getcwd()+"/certs/ca/cacert.crt")
    cc = X509.load_cert(os.getcwd()+"/certs/ca/cert.crt")
    if(not cac.verify() and 
       not cac.check_ca() and
       not cc.verify(cac.get_pubkey())):
        raise SSLError()


def generate_cert(domein):
    if(not os.path.exists(os.getcwd()+"/certs/"+domein)):
        # if there does not exist a folder in cwd. Make a new
        os.makedirs(os.getcwd()+"/certs/"+domein)

    pem_file = mk_temporary_cert(os.getcwd()+"/certs/ca/cacert.crt",
                                 os.getcwd()+"/certs/ca/cert.crt",domein)
    
    with open(os.getcwd()+"/certs/"+domein+"/"+domein.split(".")[1]+".pem","w") as f:
        f.write(pem_file.as_pem())    
    
        
    return os.getcwd()+"/certs/"+domein+"/"+domein.split(".")[1]+".pem"
    
class TLSinterceptionHandler:
    def __init__(self,socket,pem_file,http_type):
        # Browser connection is still in HTTP Tunnel-mode
        socket.send(http_type + " 200 OK\r\n\r\n")
        
        while True:
            print repr(socket.recv(65535))
        
