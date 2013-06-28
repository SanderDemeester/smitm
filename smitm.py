#!/usr/bin/python2.7
from handlers import *
from http import *
from logging import *
import argparse
import asyncore
import asynchat
import sys
import socket
import SimpleHTTPServer
import cgi
import signal

def setup_argument():
    parser = argparse.ArgumentParser(description="Secure mitm.")
    parser.add_argument('-q','--quiet',action='store_true',
                        required=False,
                        dest="q",
                        help='Disable information output')

    parser.add_argument('-i','--intercept',
                        metavar='list',
                        required=False,
                        dest='target',
                        nargs="+",
                        help="Target domein that should be intercepted, default is all")

    parser.add_argument('-b','--background',action='store_true',                      
                        required=False,
                        dest='b',
                        help="Run in background")

    parser.add_argument('-p','--port', action='store_const',
                        required=False,
                        dest="port",
                        const=9999,
                        default=9999,
                        help="Specify port, default=9999")
    
    sys.args = parser.parse_args();
    
def create_daemon():
    try:
        pid = os.fork()
        if pid > 0:
            exit(0)
    except OSError,e:
        exit(1)
    os.setsid()
    os.umask(0)
    try:
        pid = os.fork()
        if pid > 0:
            exit(0)
    except OSError,e:
        exit(1)
        
            
if __name__ == "__main__":
    
    setup_argument()

    if(sys.args.b):
        create_daemon()


    if(sys.args.target != None and len(sys.args.target)>1):
        print "not list"
    elif(sys.args.target != None and os.path.isfile(sys.args.target[0])):
        with open(sys.args.target[0]) as fd:
            sys.args.target_list = fd.read().splitlines()
            
    TCPRequestClient.args = sys.args
    signal.signal(signal.SIGINT | signal.SIGTERM, signal_handler.signal_handler)
    generate_filestructure()
    setup_ca()
    s = HTTPServer(9999,HTTPhandler)
    asyncore.loop()
