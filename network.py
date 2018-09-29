#!/usr/bin/env python3

import socket, threading, time, json, logging, struct, random

import glovar

from consistent import SERVER_ADDR, SERVER_PORT, CONNECTIONMAX, RECV_BUFFER, PACKETVER, HEADER_SIZE

#Connection node class
class ConnectedNode(threading.Thread):
    def __init__(self, sock, addr, logdirectory):
        threading.Thread.__init__(self)
        self.sock = sock
        self.addr = addr
        self.logdirectory = logdirectory
        
    def senddata(self, data):
        json_data = json.dumps(data)
        header = [PACKETVER, json_data.__len__()]
        headerPack = struct.pack('!2I', *header)
        packdata = headerPack + json_data.encode('utf-8')
        self.sock.send(packdata)

    def run(self):
        filename = self.logdirectory + 'msghandlelog.txt'
        self.logger = logging.getLogger(str(self.addr))
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        try:
            dataBuffer = bytes()
            while True:
                data = self.sock.recv(RECV_BUFFER)
                if data:
                    dataBuffer += data
                    while True:
                        if len(dataBuffer) < HEADER_SIZE: #数据包小于消息头部长度，跳出小循环
                            break
                        
                        headPack = struct.unpack('!2I', dataBuffer[:HEADER_SIZE])
                        bodySize = headPack[1]
                        # 分包情况处理，跳出函数继续接收数据
                        if len(dataBuffer) < HEADER_SIZE + bodySize: #数据包不完整，跳出小循环
                            break
                        # 读取消息正文的内容
                        recvdata = dataBuffer[HEADER_SIZE : HEADER_SIZE + bodySize]
                        # 数据处理
                        queue_data = [self, recvdata, self.addr]
                        glovar.msgqueue.put(queue_data)
                        # 粘包情况的处理
                        dataBuffer = dataBuffer[HEADER_SIZE + bodySize:] # 获取下一个数据包，类似于把数据pop出
#                        logcontent = ' Receive a message from: ' + str(self.addr)
#                        self.logger.info(logcontent)
                
        except Exception as e:
            self.logger.info(e)
            
        finally:
 #           logcontent = 'remove self.addr:' + str(self.addr)
 #           self.logger.info(logcontent)
            glovar.conLock.acquire()
            glovar.CONNECTEDADDR_LIST.remove(self.addr)
            glovar.CONNECTION_LIST.remove(self)
            glovar.CONNECTION_NUMBER -= 1
            glovar.conLock.release()
            logcontent = 'Host:' + str(self.addr) + 'disconnected from localhost.' + str(glovar.CONNECTION_NUMBER) + 'hosts terminal is still connected.'
            self.logger.info(logcontent)
            self.sock.close()
            
# Server Node
class TcpServer(threading.Thread):
    def __init__(self, tcpaddr, tcpport, maxnumber, logdirectory):
        threading.Thread.__init__(self)
        self.tcpaddr = tcpaddr
        self.tcpport = tcpport
        self.maxnumber = maxnumber
        self.logdirectory = logdirectory
        
    def run(self):
        filename = self.logdirectory + 'networklog.txt'
        self.logger = logging.getLogger('TcpServer')
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # If the default tcp port is already in use, port puls 1 until one tcp port has been binded
        try:
            server_socket.bind((self.tcpaddr, self.tcpport))
            # glovar.BINDED_ADDR = glovar.BINDED_ADDR + (self.tcpaddr, self.tcpport)
            logcontent = 'Bind local port: (' + str(self.tcpaddr) + ',' + str(self.tcpport) + ')'
            self.logger.info(logcontent)
        except OSError as err:
            logcontent = 'Port:' + str(self.tcpport) + 'is already in use!'
            self.logger.info(logcontent)
            raise
                    
        server_socket.listen(self.maxnumber)

        while True:
            if glovar.CONNECTION_NUMBER == self.maxnumber:
                time.sleep(5)
            else:
                #print('CONNECTION_NUMBER:', CONNECTION_NUMBER)
                sockfd, addr = server_socket.accept()
                socket_accept_thread = threading.Thread(target=self.__socket_accept, args=(sockfd, addr))
                socket_accept_thread.start()

        server_socket.close()  # Close server

    #Connection acceptance process
    def __socket_accept(self, sockfd, addr):
        user = ConnectedNode(sockfd, addr, self.logdirectory)
        glovar.conLock.acquire()
        glovar.CONNECTION_LIST.append(user)
        glovar.CONNECTEDADDR_LIST.append(addr)
        glovar.CONNECTION_NUMBER += 1
        glovar.conLock.release()
        user.start()
        
#        timelog = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' '
#        print(timelog, 'Host: %s connected in. %d connections has established.' % (addr, glovar.CONNECTION_NUMBER))             
        logcontent = 'Host:' + str(addr) + 'connected in. ' + str(glovar.CONNECTION_NUMBER) + ' connections has established.'
        self.logger.info(logcontent)
        logcontent = 'Current CONNECTEDADDR_LIST is:' + str(glovar.CONNECTEDADDR_LIST)
        self.logger.info(logcontent)
        
# Connect to node in the NODE_LIST              
class ConnectionCreation(threading.Thread):
    def __init__(self, logdirectory):
        threading.Thread.__init__(self)
        self.logdirectory = logdirectory
        
    def run(self):
        filename = self.logdirectory + 'networklog.txt'
        self.logger = logging.getLogger('ConnectionCreation')
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        NODE_LIST = glovar.confnode
        
        while True:
            for each in NODE_LIST:
                if each not in glovar.CONNECTEDADDR_LIST:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        sock.connect(each)
                        user = ConnectedNode(sock, each, self.logdirectory)
                    
                        glovar.conLock.acquire()
                        glovar.CONNECTEDADDR_LIST.append(each)
                        glovar.CONNECTION_LIST.append(user)
                        glovar.CONNECTION_NUMBER += 1
                        glovar.conLock.release()
                        user.start()
                        logcontent = 'Success to connect to host:' + str(each) + '. ' +  str(glovar.CONNECTION_NUMBER) + ' connections has established.'
                        self.logger.info(logcontent)
                        logcontent = 'Current CONNECTEDADDR_LIST is:' + str(glovar.CONNECTEDADDR_LIST)
                        self.logger.info(logcontent)
                                
                    except ConnectionRefusedError:
                        time.sleep(0.5)
            
            time.sleep(5)

# Broadcast message class
class BroadMsg(threading.Thread):
    def __init__(self, logdirectory):
        threading.Thread.__init__(self)
        self.logdirectory = logdirectory
                        
    def run(self):
        filename = self.logdirectory + 'networklog.txt'
        self.logger = logging.getLogger('BroadMsg')
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info('Start broadcast message thread process.')
        while True:
            try:
                #glovar.broadLock.acquire()
                sendmsg = glovar.broadqueue.get()
                #glovar.broadLock.release()
                #self.logger.info('get a message from broadqueue.')
                for each in  glovar.CONNECTION_LIST:
                    time.sleep(random.uniform(0,0.1))
                    each.senddata(sendmsg)
#                    logcontent = 'Send message: ' + str(sendmsg) + ' to ' + str(each.addr)
#                    self.logger.info(logcontent)
            except Exception as e:
                self.logger.info("----------------------")
                self.logger.info(e)
                self.logger.info(sendmsg)
                self.logger.info("------------------------")
                raise e

# Broad a message into the network
def broadMessage(senddata):
    glovar.broadLock.acquire()
    glovar.broadqueue.put(senddata)
    glovar.broadLock.release()

# function test         
if __name__ == '__main__':
    tcp_server = TcpServer(SERVER_ADDR, SERVER_PORT, CONNECTIONMAX)
    tcp_server.start()
    time.sleep(2)
    tcp_connect = ConnectionCreation()
    tcp_connect.start()

