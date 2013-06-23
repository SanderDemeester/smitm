import signal
import sys

def signal_handler(signal,frame):
    print "Request exit"
    sys.exit(0)


