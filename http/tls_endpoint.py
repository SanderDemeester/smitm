import socket
import ssl
import time
import select
import os
import asynchat
import asyncore
import BaseHTTPServer
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

    (cert,key) = mk_temporary_cert(os.getcwd()+"/certs/ca/cacert.crt",
                                 os.getcwd()+"/certs/ca/cert.crt",domein)
    
    with open(os.getcwd()+"/certs/"+domein+"/"+domein.split(".")[1]+".pem","w") as f:
        f.write(cert.as_pem())    
        
    with open(os.getcwd()+"/certs/"+domein+"/"+domein.split(".")[1]+".key","w") as f:
        f.write(key.as_pem(None))

    # openssl x509 -in file.pem -text
    return (os.getcwd()+"/certs/"+domein+"/"+domein.split(".")[1]+".pem",
            os.getcwd()+"/certs/"+domein+"/"+domein.split(".")[1]+".key")
    

class SSLLocalServer(asyncore.dispatcher):
    def __init__(self,local_socket,pem_file,key_file):
        asyncore.dispatcher.__init__(self)
        self.socket = ssl.wrap_socket(local_socket,server_side=True,
                                      certfile=pem_file,
                                      keyfile=key_file,
                                      do_handshake_on_connect=False)

        while True:
            try:
                self.socket.do_handshake()
                break
            except ssl.SSLError, err:
                if err.args[0] == ssl.SSL_ERROR_WANT_READ:
                    select.select([self.socket],[],[])
                elif err.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                    select.select([],[self.socket],[])
                else:
                    raise
            

    def handle_read(self):
        print "read"

    def handle_write(self):
        print "write"
        
def ssl_wrapper(browser_socket,pem_file,key_file):
    # create ssl context
    # ctx = SSL.Context(SSL.SSLv23_METHOD)
    # ctx.use_privatekey_file(key_file)
    # ctx.use_certificate_file(pem_file)
    # ctx.load_verify_locations(pem_file)

    # ssl_browser_connection = SSL.Connection(ctx,browser_socket)
    # ssl_browser_connection.set_accept_state()
    
    ssl_browser_connection = ssl.wrap_socket(browser_socket,
                                             server_side=True,
                                             certfile=pem_file,
                                             keyfile=key_file)
    
    return ssl_browser_connection
            

