import asyncore
import asynchat
import sys
import socket
import SimpleHTTPServer
import cgi
from OpenSSL import crypto,SSL
from tls_endpoint import *

class TCPRequestClient(asyncore.dispatcher):
    """HTTP Tunneling behind a web proxy"""
    # we will use the asyncore dispatcher for handeling
    # traffic from proxy to remote server (proxy<->server)

    def __init__(self,connection,addr,header_list,handler):
        asyncore.dispatcher.__init__(self)
        self.header_dict = {}
        for list in header_list:
            if(len(list)==2):
                self.header_dict.update(dict(zip(list[0::2],list[1::2])))
            else:
                list = [list[0],' '.join(list[1:])]
                self.header_dict.update(dict(zip(list[0::2],list[1::2])))
        self.local_socket = connection # socket browser<->proxy
        self.local_addres = addr # addres from browser<->proxy
        self.original_handler = handler # the original handler
        
        (self.hostname,self.port) = self.header_dict['CONNECT'].split(' ')[0].split(':')

        # setup passthroug
        self.http_type = self.header_dict['CONNECT'].split(' ')[1]

        # for on the fly intercetion comment this
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connect((self.hostname,int(self.port)))

        #intercept test code
        # Generate on the fly a certificate for this domein
        (self.pem_file,self.key_file) = generate_cert(self.hostname)
        #print self.pem_file

        # Implement RFC 2817 section 5.3
        self.local_socket.send(self.http_type + " 200 OK\r\n\r\n")
        
        #for on the fly interception, uncomment this
        # self.ssl_local_server = SSLLocalServer(self.local_socket,
        #                                       self.pem_file,
        #                                       self.key_file)

        self.out_buffer = ""
    
    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()
    
    def handle_read(self):
        buffer = self.recv(10000)
        self.original_handler.push(buffer)
        buffer = ""
    
    def handle_write(self):
        sent = self.send(self.out_buffer)
        self.out_buffer = self.out_buffer[sent:]

    def feed(self,data):
        self.out_buffer += data

    def writable(self):
        return (len(self.out_buffer)>0)
    
        

class HTTPRequestClient(asyncore.dispatcher,SimpleHTTPServer.SimpleHTTPRequestHandler):
    # This class should connect to the remote server and pass all data received from the local client

    def __init__(self,host,request,HTTPhandler):
        asyncore.dispatcher.__init__(self)
        #print "INIT-HTTPRequesetClient"
        if(len(host.split(":")) == 2):
            (self.hostname,self.port) = host.split(":")
        else:
            self.hostname = host
            self.port = 80
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        if(self.hostname == "127.0.0.1"):
            self.log_info("server does not accept connections back to itself")
            raise asyncore.ExitNow("Server will halt - sorry about that")
        self.connect((self.hostname,int(self.port)))
        self.in_buffer = ""
        self.out_buffer = request
        self.http_handler = HTTPhandler
    
    def handle_connect(self):
        pass

    def handle_error(self):
        print "some error"

    def handle_close(self):
        #print "closing HTTPRequestHandler"
        self.close()
    
    def handle_read(self):
        buffer = self.recv(10000)
        #print buffer        
        self.http_handler.push(buffer)
        buffer = ""

    def handle_write(self): 
        #sent contains the number of bytes sent
        sent = self.send(self.out_buffer)
        
        #save in buffer the bytes that have not been sent
        self.out_buffer = self.out_buffer[sent:] 
        self.send("\r\n\r\n")

    def feed(self,data):
        self.out_buffer += data
    
    def writable(self):
        return (len(self.out_buffer)>0)

class HTTPhandler(asynchat.async_chat,SimpleHTTPServer.SimpleHTTPRequestHandler):
    
    """This class handels all requests from the local browser"""
    # we do not use push_with_procucer because we do not know when the producer will be ready.
    def __init__(self,connection,addr,server):
        asynchat.async_chat.__init__(self,connection)
        #print "INIT-HTTPhandler"
        self.client_addr = addr
        self.connection = connection
        self.server = server
        self.data = ""
        self.set_terminator('\r\n\r\n')
        self.found_terminator = self.handle_request_line
        self.request_version = "HTTP/1.1"
        self.init = 0 # flag to see if our request handler is already init
        self.tcp_streaming_flag = 0 # flag to see if our HTTPhandler is in tcp streaming mode
        
    def collect_incoming_data(self,data):
        self.data += data
        if(self.tcp_streaming_flag == 1):
            self.http_request_handler.feed(self.data)
            self.data = "" # clear out our buffers
    
    def collect_incoming_data_tcp_mode(self):
        self.collect_incoming_data(self,self.data)
            
    
    def handle_request_line(self):
        header_array = self.data.split("\r\n")
        header_list = [i.split() for i in header_array]
        for header in header_list:
            if(header[0] == 'Host:'):
                host = header[1]
            elif(header[0] == "GET"):
                print "GET: " + header[1]
            elif(header[0] == "CONNECT"):
                print "TUNNEL-REQU: " + header[1].split(':')[0]
                self.tcp_streaming_flag = 1

        #print "request for: " + host
        #print self.data
        if(self.init == 0):
            try:
                if(self.tcp_streaming_flag == 1):
                    #self.connection contains the socket: client->proxy
                    #self.addr contains the addres bound to the socket
                    #header_list contains a list for the HTTP headers
                    self.http_request_handler = TCPRequestClient(self.connection,self.client_addr,
                                                                 header_list,self)
                    # when we are in tcp streaming mode we will ignore any terminator
                    # and forward all tcp traffic ourself.
                    # the terminator methode should no longer be used because all our traffic
                    # will now be opic TCP traffic (mostly TLS/SSL)
                    self.found_terminator = self.collect_incoming_data_tcp_mode
                    self.data = ""
                else:
                    #host contains the value from the http host header
                    #self.data contains the original http request
                    self.http_request_handler = HTTPRequestClient(host,self.data,self)
                self.init = 1
                self.http_request_handler.init = 1
            except asyncore.ExitNow:
                #print "FOUT!!!"
                self.push("smitm error")
        else:
            #print self.http_request_handler
            self.http_request_handler.feed(self.data)
            #clear out data buffer
            self.data = ""

class HTTPServer(asyncore.dispatcher):
    def __init__(self,port,handler):        
        asyncore.dispatcher.__init__(self)
        print "INIT-smitm proxy server"
        self.port = port
        self.handler = handler
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('',port))
        self.listen(5)

    def handle_accept(self):
        try:
            (connection,addr) = self.accept()
        except socket.error:
            self.log_info("server accept() error")
            return
        except TypeError:
            self.log_info("server accept() threw blocking error")
            return
        self.handler(connection,addr,self)
