from OpenSSL import crypto
from OpenSSL import SSL
from time import gmtime
from time import mktime

def create_cert(CN):
    """Create self-signed certificate."""
    
    # create a key pair                                                                                                                                                       
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 1024)
    
    # create a self-signed cert                                                                                                                                               
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "Minnesota"
    cert.get_subject().L = "Minnetonka"
    cert.get_subject().O = "my company"
    cert.get_subject().OU = "my organization"
    cert.get_subject().CN = CN
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha1')

    return (cert,k)
    

