#!/usr/bin/env python

import socket, asyncore, logging, sys

MAX_CLIENT_NUM = 100
BUF_SIZE = 4096

main_clients = []

def add_proxy_socket(proxy_socket):
    global main_clients
    size = len(main_clients)
    logging.debug('The size of main_clients before adding = %d' % size)
    main_clients.append(proxy_socket)
    size = len(main_clients)
    logging.debug('The size of main_clients after adding = %d' % size)

def remove_proxy_socket(proxy_socket):
    global main_clients
    size = len(main_clients)
    logging.debug('The size of main_clients before removing = %d' % size)
    main_clients = filter(lambda temp_socket: temp_socket != proxy_socket, main_clients)
    size = len(main_clients)
    logging.debug('The size of main_clients after removing = %d' % size)

class ProxySocket(asyncore.dispatcher):
    def __init__(self, sock, name, remote_info=None, client_addr=None):
        asyncore.dispatcher.__init__(self, sock)
        
        self.logger = logging.getLogger('ProxySocket %s' % str(name))
        
        if remote_info:
            msg = "remote_info = %s" % remote_info
            self.logger.debug(msg)
            self.connect((remote_info[0], remote_info[1]))
        
        self.client_addr = None
        if client_addr:
            self.client_addr = client_addr
        
        self.counterpart = None
        
        self.bytes_read = 0
        self.bytes_sent = 0
        
        self.logger.debug("Done with __init__")
    
    def set_counterpart(self, counterpart):
        self.counterpart = counterpart
    
    def handle_connect(self):
        self.logger.debug("handle_connect()")
    
    def handle_read(self):
        self.logger.debug("handle_read()")
        
        buff = self.recv(BUF_SIZE)
        buff_size = len(buff)
        self.logger.debug("Received %d bytes" % buff_size)
        self.bytes_read += buff_size
        
        if 0 == buff_size:
            self.counterpart.handle_close()
        
        if self.counterpart:
            try:
                self.counterpart.send(buff)
                self.bytes_sent += buff_size
            except:
                self.logger.debug('Could not write to the counterpart')
                self.handle_close()
    
    def handle_close(self):
        self.logger.debug("handle_close()")
        self.logger.debug('Total bytes read = %d' % self.bytes_read)
        self.logger.debug('Total bytes sent = %d' % self.bytes_sent)
        self.close()

class MainClientSocket(ProxySocket):
    def handle_close(self):
        self.logger.debug("handle_close()")
        self.logger.debug('Total bytes read = %d' % self.bytes_read)
        self.logger.debug('Total bytes sent = %d' % self.bytes_sent)
        self.close()
        remove_proxy_socket(self)

class InjectionSocket(asyncore.dispatcher):
    def __init__(self, sock, name):
        asyncore.dispatcher.__init__(self, sock)
        
        self.logger = logging.getLogger('InjectionSocket %s' % str(name))
        
        self.bytes_read = 0
        self.bytes_sent = 0
        
        self.logger.debug("Done with __init__")
    
    def handle_connect(self):
        self.logger.debug("handle_connect()")
    
    def handle_read(self):
        self.logger.debug("handle_read()")
        
        buff = self.recv(BUF_SIZE)
        buff_size = len(buff)
        self.logger.debug("Received %d bytes" % buff_size)
        self.bytes_read += buff_size
        
        global main_clients
        for client in main_clients:
            try:
                client.send(buff)
                self.logger.debug(
                    'Sent %d bytes to the client %s'
                    % (buff_size, client.client_addr)
                )
                self.bytes_sent += buff_size
            except:
                self.logger.debug(
                    'Could not write to the client %s'
                    % client.client_addr
                )
    
    def handle_close(self):
        self.logger.debug("handle_close()")
        self.logger.debug('Total bytes read = %d' % self.bytes_read)
        self.logger.debug('Total bytes sent = %d' % self.bytes_sent)
        self.close()

class TcpInjectionServer(asyncore.dispatcher):
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        
        self.logger = logging.getLogger('TcpInjectionServer')
        
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        #  This must come before binding
        self.set_reuse_addr()
        self.bind(address)
        # Remember to listen before you talk!!!
        self.listen(MAX_CLIENT_NUM)
        self.logger.debug(
            'Successfully bound to the auxiliary %s:%d'
            % (address[0], address[1])
        )
        
        self.handlerCount = 0
        
        self.logger.debug("Done with __init__")
    
    def handle_accept(self):
        self.logger.debug("handle_accept()")
        
        client_info = self.accept()
        if client_info:
            client_sock, client_addr = client_info
            
            self.handlerCount += 1
            
            try:
                client_name = 'Client %d' % self.handlerCount
                inject_client = InjectionSocket(client_sock, client_name)
            except Exception:
                sys.stderr.write('Something really bad happened! inject_client :(\n')
        else:
            self.logger.debug("Nothing to accept :(")
            self.close()

class TcpProxyServer(asyncore.dispatcher):
    def __init__(self, address, remote_info, inject_port = -1):
        asyncore.dispatcher.__init__(self)
        
        self.logger = logging.getLogger('TcpProxyServer')
        
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        #  This must come before binding
        self.set_reuse_addr()
        self.bind(address)
        # Remember to listen before you talk!!!
        self.listen(MAX_CLIENT_NUM)
        self.logger.debug(
            'Successfully bound to the main %s:%d'
            % (address[0], address[1])
        )
        
        self.remote_info = remote_info
        
        if inject_port >= 0:
            self.logger.debug("Initializing auxiliary server")
            inject_addr = (address[0], inject_port)
            self.inject_server = TcpInjectionServer(inject_addr)
        else:
            self.logger.debug("No auxiliary server required")
        
        self.handlerCount = 0
        
        self.logger.debug("Done with __init__")
    
    def handle_accept(self):
        self.logger.debug("handle_accept()")
        
        client_info = self.accept()
        if client_info:
            client_sock, client_addr = client_info
            
            self.handlerCount += 1
            
            try:
                client_name = 'Client %d' % self.handlerCount
                main_client = MainClientSocket(client_sock, client_name, None, client_addr)
            except Exception:
                sys.stderr.write('Something really bad happened! main_client :(\n')
            
            try:
                forwarder_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                forwarder_name = 'Forwarder %d' % self.handlerCount
                forwarder = ProxySocket(forwarder_sock, forwarder_name, self.remote_info)
            except Exception:
                sys.stderr.write('Something really bad happened! forwarder :(\n')
            
            main_client.set_counterpart(forwarder)
            forwarder.set_counterpart(main_client)
            
            add_proxy_socket(main_client)
        else:
            self.logger.debug("Nothing to accept :(")
            self.close()
    
    def handle_connect(self):
        self.logger.debug("handle_connect()")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')
    
    if (len(sys.argv) < 3) or (len(sys.argv) > 4):
        logging.debug(
            'Usage: %s <main_port> <remote_addr:remote_port> [inject_port]'
            % sys.argv[0]
        )
        exit(1)
    
    main_port = int(float(sys.argv[1]))
    remote_info = sys.argv[2].split(':')
    remote_info[1] = int(float(remote_info[1]))
    inject_port = -1
    
    if len(sys.argv) == 4:
        inject_port = int(float(sys.argv[3]))
    
    address = ('0.0.0.0', main_port)
    logging.debug("Initializing a TcpProxyServer instance")
    echoServer = TcpProxyServer(address, remote_info, inject_port)
    
    logging.debug("Before the LOOP")
    asyncore.loop()
    logging.debug("After the LOOP")
