import asyncore
import asynchat
import sys
import socket
import SimpleHTTPServer
import cgi

class TCPRequestClient(asyncore.dispatcher):
    """HTTP Tunneling behind a web proxy"""
    def __init__(self,host,request,HTTPhandler):
        asyncore.dispatcher.__init__(self)
        print host
    
    def handle_connect(self):
        pass

    def handle_error(self):
        print "some error from TCPRequestClient"
        
    def handle_close(self):
        print "closing TCPRequestClient"
        self.close()
    
    def handle_read(self):
        buffer = self.recv(10000)
        self.http_handler.push(buffer)
        buffer = ""
    
    def handle_write(self):
        sent = self.send(self.out_buffer)
        self.out_buffer = self.out_buffer[sent:]

    def feef(self,data):
        self.out_buffer += data

    def writable(self):
        return (len(self.out_buffer)>0)
    
        

class HTTPRequestClient(asyncore.dispatcher,SimpleHTTPServer.SimpleHTTPRequestHandler):
    # This class should connect to the remote server and pass all data received from the local client

    def __init__(self,host,request,HTTPhandler):
        asyncore.dispatcher.__init__(self)
        print "INIT-HTTPRequesetClient"
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
        print "closing HTTPRequestHandler"
        self.close()
    
    def handle_read(self):
        buffer = self.recv(10000)
#        print buffer        
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
        print "INIT-HTTPhandler"
        self.client_addr = addr
        self.connection = connection
        self.server = server
        self.data = ""
        self.set_terminator('\r\n\r\n')
        self.found_terminator = self.handle_request_line
        self.request_version = "HTTP/1.1"
        self.init = 0
        
    def collect_incoming_data(self,data):
        self.data += data
    
    def handle_request_line(self):
        header_array = self.data.split("\r\n")
        header_list = [i.split() for i in header_array]
        tcp_streaming_flag = 0
        for header in header_list:
            if(header[0] == 'Host:'):
                host = header[1]
            elif(header[0] == "GET"):
                print "GET: " + header[1]
            elif(header[0] == "CONNECT"):
                tcp_streaming_flag = 1

        print "request for: " + host
#        print self.data
        if(self.init == 0):
            try:
                if(tcp_streaming_flag == 1):
                    self.http_request_handler = TCPRequestClient(host,self.data,self)
                else:
                    self.http_request_handler = HTTPRequestClient(host,self.data,self)
                self.init = 1
                self.http_request_handler.init = 1
            except asyncore.ExitNow:
                print "FOUT!!!"
                self.push("smitm error")
        else:
            print self.http_request_handler
            self.http_request_handler.feed(self.data)

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
