import shutil
import os
import signal
import sys

def signal_handler(signal,frame):
    print "Request exit"
    shutil.rmtree(os.getcwd()+"/certs")
    sys.exit(0)


