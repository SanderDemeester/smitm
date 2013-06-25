import socket
import ssl
import time
import os
import asynchat
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
    

def ssl_wrapper(browser_socket,pem_file,key_file):
    # create ssl context
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.use_privatekey_file(key_file)
    ctx.use_certificate_file(pem_file)
    ctx.load_verify_locations(pem_file)

    ssl_browser_connection = SSL.Connection(ctx,browser_socket)
    ssl_browser_connection.set_accept_state()

    return ssl_browser_connection
            
class HTTPServerWrapper(BaseHTTPServer.HTTPServer):
    def __init__(self,handler,chainHandler):
        self.RequestHandlerClass = handler
        self.chainedHandler = chainHandler

class SSLConnectionWrapper(object):
    def __init__(self, conn, socket):
        self._connection = conn
        self._socket = socket
        
	def __getattr__(self, name):
            return self._connection.__getattribute__(name)
        
	def __str__(self):
            return object.__str__(self)
        
	def __repr__(self):
            return object.__repr__(self)
        
	def recv(self, amount):
            return self._wrap(self._socket, self._connection.recv, 10, amount)
        
	def send(self, data):
            return self._wrap(self._socket, self._connection.send, 10, data)
        
	def makefile(self, perm, buf):
            return SSLConnectionWrapperFile(self, socket)
        
	def _wrap(self, socket, fun, attempts, *params):
            count = 0
            
            while True:
                try:
                    result = fun(*params)
                    
                    break
                except OpenSSL.SSL.WantReadError:
                    count += 1
                    
                    if count == attempts:
                        break
                    
                    select.select([socket], [], [], 3)
                except OpenSSL.SSL.WantWriteError:
                    count += 1
                    
                    if count == attempts:
                        break                    
                select.select([], [socket], [], 3)

            return result
