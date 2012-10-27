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
    def __init__(self, sock, name, remote_info=None):
        asyncore.dispatcher.__init__(self, sock)
        
        self.logger = logging.getLogger('ProxySocket %s' % str(name))
        
        if remote_info:
            msg = "remote_info = %s" % remote_info
            self.logger.debug(msg)
            self.connect((remote_info[0], remote_info[1]))
        
        self.counterpart = None
        
        self.logger.debug("Done with __init__")
    
    def set_counterpart(self, counterpart):
        self.counterpart = counterpart
    
    def handle_connect(self):
        self.logger.debug("handle_connect()")
    
    def handle_read(self):
        self.logger.debug("handle_read()")
        
        buff = self.recv(BUF_SIZE)
        self.logger.debug("Received %d bytes" % len(buff))
        
        if self.counterpart:
            try:
                self.counterpart.send(buff)
            except:
                self.logger.debug('Could not write to the counterpart')
    
    def handle_close(self):
        self.logger.debug("handle_close()")
        self.close()

class MainClientSocket(ProxySocket):
    def handle_close(self):
        self.logger.debug("handle_close()")
        self.close()
        remove_proxy_socket(self)

class AuxSocket(asyncore.dispatcher):
    def __init__(self, sock, name):
        asyncore.dispatcher.__init__(self, sock)
        
        self.logger = logging.getLogger('AuxSocket %s' % str(name))
        
        self.logger.debug("Done with __init__")
    
    def handle_connect(self):
        self.logger.debug("handle_connect()")
    
    def handle_read(self):
        self.logger.debug("handle_read()")
        
        buff = self.recv(BUF_SIZE)
        self.logger.debug("Received %d bytes" % len(buff))
        
        global main_clients
        for client in main_clients:
            client.send(buff)
    
    def handle_close(self):
        self.logger.debug("handle_close()")
        self.close()

class TcpAuxServer(asyncore.dispatcher):
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        
        self.logger = logging.getLogger('TcpAuxServer')
        
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
                aux_client = AuxSocket(client_sock, client_name)
            except Exception:
                sys.stderr.write('Something really bad happened! aux_client :(\n')
        else:
            self.logger.debug("Nothing to accept :(")
            self.close()

class TcpProxyServer(asyncore.dispatcher):
    def __init__(self, address, remote_info, aux_port = -1):
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
        
        if aux_port >= 0:
            self.logger.debug("Initializing auxiliary server")
            aux_addr = (address[0], aux_port)
            self.aux_server = TcpAuxServer(aux_addr)
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
                main_client = MainClientSocket(client_sock, client_name)
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
            'Usage: %s <main_port> <remote_addr:remote_port> [aux_port]'
            % sys.argv[0]
        )
        exit(1)
    
    main_port = int(float(sys.argv[1]))
    remote_info = sys.argv[2].split(':')
    remote_info[1] = int(float(remote_info[1]))
    aux_port = -1
    
    if len(sys.argv) == 4:
        aux_port = int(float(sys.argv[3]))
    
    address = ('0.0.0.0', main_port)
    logging.debug("Initializing a TcpProxyServer instance")
    echoServer = TcpProxyServer(address, remote_info, aux_port)
    
    logging.debug("Before the LOOP")
    asyncore.loop()
    logging.debug("After the LOOP")
