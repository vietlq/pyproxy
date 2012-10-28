#!/usr/bin/env python

import socket, asyncore, logging, sys

MAX_CLIENT_NUM = 100
BUF_SIZE = 4096

class EchoHandler(asyncore.dispatcher):
    def __init__(self, sock, name):
        asyncore.dispatcher.__init__(self, sock)
        
        self.logger = logging.getLogger('EchoHandler %s' % str(name))
        
        self.bytes_read = 0
        self.bytes_sent = 0
        
        self.write_buffer = ''
        self.read_buffer = ''
        
        self.logger.debug("Done with __init__")
    
    def handle_connect(self):
        self.logger.debug("handle_connect()")
    
    def handle_read(self):
        self.logger.debug("handle_read()")
        
        buff = self.recv(BUF_SIZE)
        buff_size = len(buff)
        self.logger.debug("Received %d bytes" % buff_size)
        self.bytes_read += buff_size
        
        try:
            self.write_buffer += buff
        except:
            self.logger.debug("Could not write!")
    
    def writable(self):
        is_writable = (len(self.write_buffer) > 0)
        if is_writable:
            self.logger.debug('writable() -> %s', is_writable)
        return is_writable

    def handle_write(self):
        bytes_sent = self.send(self.write_buffer)
        self.logger.debug('handle_write() -> sent %s bytes', bytes_sent)
        self.write_buffer = self.write_buffer[bytes_sent:]
        self.bytes_sent += bytes_sent
    
    def handle_close(self):
        self.logger.debug("handle_close()")
        self.logger.debug('Total bytes read = %d' % self.bytes_read)
        self.logger.debug('Total bytes sent = %d' % self.bytes_sent)
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
