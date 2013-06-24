#!/usr/bin/python2.7
from handlers import *
from http import *
from logging import *
import asyncore
import asynchat
import sys
import socket
import SimpleHTTPServer
import cgi
import signal

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler.signal_handler)
    generate_filestructure()
    s = HTTPServer(9999,HTTPhandler)
    asyncore.loop()
