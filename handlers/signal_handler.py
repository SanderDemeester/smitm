import shutil
import os
import signal
import sys

def signal_handler(signal,frame):
    print "Request exit"
    if(os.path.exists(os.getcwd()+"/certs")):
        # If we did not see any TLS/SSL connections, then this folder will not exist
        shutil.rmtree(os.getcwd()+"/certs")
    
    shutil.rmtree(os.getcwd()+"/http_logging")
    sys.exit(0)


