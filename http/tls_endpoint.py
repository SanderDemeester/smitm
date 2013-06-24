import socket
import ssl
import time
import os
from random import randint
from OpenSSL import crypto,SSL
def generate_cert(domein):
    if(not os.path.exists(os.getcwd()+"/certs/"+domein)):
        # if there does not exist a folder in cwd. Make a new
        os.makedirs(os.getcwd()+"/certs/"+domein)

    
    # Make keypair
    key_pair = crypto.PKey()
    key_pair.generate_key(crypto.TYPE_RSA,2048)

    # Make certificate
    certificate = crypto.X509()
    certificate.get_subject().C = "BE"
    certificate.get_subject().ST = "Ghent"
    certificate.get_subject().L = "Flemish"
    certificate.get_subject().O = "ugent"
    certificate.get_subject().OU = "ugent"
    certificate.get_subject().CN = domein
    certificate.set_serial_number(randint(1,65536))
    
    certificate.set_issuer(certificate.get_subject())
    certificate.set_pubkey(key_pair)
    certificate.sign(key_pair,'sha1')
    
    certificate_fd = os.open(os.path.join(os.getcwd()+"/certs/"+domein,domein.split('.')[1]+".crt"),os.O_RDWR|os.O_CREAT)    
    privatekey_fd = os.open(os.path.join(os.getcwd()+"/certs/"+domein,domein.split(".")[1]+".key"), os.O_RDWR|os.O_CREAT)
    
    os.write(certificate_fd,crypto.dump_certificate(crypto.FILETYPE_PEM,certificate))
    os.write(privatekey_fd, crypto.dump_privatekey(crypto.FILETYPE_PEM,key_pair))
    
