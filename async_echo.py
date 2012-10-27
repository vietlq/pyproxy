#!/usr/bin/env python

import socket, asyncore, logging, sys

MAX_CLIENT_NUM = 100
BUF_SIZE = 4096

class EchoHandler(asyncore.dispatcher):
    def __init__(self, sock, name):
        asyncore.dispatcher.__init__(self, sock)
        
        self.logger = logging.getLogger('EchoHandler %s' % str(name))
        
        self.logger.debug("Done with __init__")
    
    def handle_connect(self):
        self.logger.debug("handle_connect()")
    
    def handle_read(self):
        self.logger.debug("handle_read()")
        buff = self.recv(BUF_SIZE)
        self.logger.debug("Received %d bytes" % len(buff))
        try:
            self.send(buff)
        except:
            self.logger.debug("Could not write!")
    
    def handle_close(self):
        self.logger.debug("handle_close()")
        self.close()
    

class EchoServer(asyncore.dispatcher):
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        
        self.logger = logging.getLogger('EchoServer')
        
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(address)
        # Remember to listen before you talk!!!
        self.listen(MAX_CLIENT_NUM)
        
        self.handlerCount = 0
        
        self.logger.debug("Done with __init__")
    
    def handle_accept(self):
        self.logger.debug("handle_accept()")
        
        client_info = self.accept()
        if client_info:
            sock, addr = client_info
            
            self.handlerCount += 1
            
            aHandler = EchoHandler(sock, self.handlerCount)
        else:
            self.logger.debug("Nothing to accept :(")
            self.close()
    
    def handle_connect(self):
        self.logger.debug("handle_connect()")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')
    
    if len(sys.argv) != 3:
        sys.stderr.write('Usage: %s <host_name> <port_number>\n')
        exit(1)
    
    host_name = sys.argv[1]
    port_number = int(float(sys.argv[2]))
    
    address = (host_name, port_number)
    logging.debug("Initializing an EchoServer instance")
    echoServer = EchoServer(address)
    
    logging.debug("Before the LOOP")
    asyncore.loop()
    logging.debug("After the LOOP")
