from OpenSSL import SSL
from OpenSSL import crypto
from time import gmtime
from time import mktime
import M2Crypto
import ssl

def create_cert(hostname):
    """Create self-signed certificate."""    

    # Fetch the X509 certificate to get all values for our fake certificate
    target_cert = ssl.get_server_certificate((hostname, 443))
    target_x509 = M2Crypto.X509.load_cert_string(target_cert)
    # create a key pair                                                                                                                                                       
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 1024)
    
    # create a self-signed cert                                                                                                                                               
    cert = crypto.X509()
    
    if target_x509.get_subject().C:
        cert.get_subject().C = str(target_x509.get_subject().C)
    if target_x509.get_subject().ST:
        cert.get_subject().ST = str(target_x509.get_subject().ST)
    if target_x509.get_subject().L:
        cert.get_subject().L = str(target_x509.get_subject().L)
    if target_x509.get_subject().O:        
        cert.get_subject().O = str(target_x509.get_subject().O)
    if target_x509.get_subject().CN:
        cert.get_subject().CN = str(target_x509.get_subject().CN)

    cert.set_serial_number(target_x509.get_serial_number())
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha1')

    return (cert,k)
    

