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
from cert_generate import create_cert
from os.path import join

def generate_cert(domein):
    if(not os.path.exists(os.getcwd()+"/certs/"+domein)):
        # if there does not exist a folder in cwd. Make a new
        os.makedirs(os.getcwd()+"/certs/"+domein)
        
    cert_name = domein.split(".")[len(domein.split("."))-2]
    (cert,key) = create_cert(domein)
    
    open(join("%s/certs/%s/%s.crt" % (os.getcwd(), domein, cert_name)), "wt").write(
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    open(join("%s/certs/%s/%s.key" % (os.getcwd(), domein, cert_name)), "wt").write(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    # openssl x509 -in file.pem -text
    return (os.getcwd()+"/certs/"+domein+"/"+cert_name+".crt",
            os.getcwd()+"/certs/"+domein+"/"+cert_name+".key")
    

class SSLLocalServer(asyncore.dispatcher):
    def __init__(self,local_socket, cert_file, key_file):
        asyncore.dispatcher.__init__(self)
        
        print cert_file
        print key_file

        self.socket = ssl.wrap_socket(local_socket,
                                      server_side=True,
                                      certfile=cert_file,
                                      keyfile=key_file,                                      
                                      ssl_version=ssl.PROTOCOL_TLSv1,
                                      do_handshake_on_connect=False)
        # Do ssl handshake
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
        pass

    def handle_write(self):
        pass
        
