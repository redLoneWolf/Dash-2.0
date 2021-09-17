# from numpy.lib.financial import ipmt
# from protocol import Commands
# from protocol import Protocol
import logging
from typing import List
from utils import getHost, getPort
from PyQt5.QtCore import  QObject

from PyQt5.QtNetwork import QHostAddress, QHostInfo, QTcpServer,QTcpSocket,QAbstractSocket
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

intDT = np.dtype(np.int32).newbyteorder('>')
floatDT = np.dtype(np.float32).newbyteorder('>')
charDT= np.dtype('U1').newbyteorder('>')
intDT8 = np.dtype(np.byte).newbyteorder('>')
import enum
import sys
from logging.handlers import RotatingFileHandler
from logging import handlers
log = logging.getLogger('hello')



class FrameReceiverThread(QThread):
    PREAMBLE = ord('$')
    onData = pyqtSignal(bytes)

    def __init__(self,client:QTcpSocket,parent=None):
        super().__init__(parent=parent)
        self.client = client
        self.gotPreamble = False
        self.gotSize = False
        self.gotCommand = False
        self.gotData = False
        

    def listen(self,client:QTcpSocket):
        while True:
            needBytes = 1
            got = client.bytesAvailable()
            # print('got',got)
            if got >= needBytes:
                if(not self.gotPreamble):
                    data = client.read(1)
                    print('pream',data)
                    preamble = np.frombuffer(data, dtype=intDT8,count=1)[0]
                    if preamble ==self.PREAMBLE:
                        self.gotPreamble = True
                        needBytes = 4
                
                elif(self.gotPreamble and not self.gotSize):
                    sizedata = client.read(4)
                    print('size',sizedata)
                    self.size = np.frombuffer(sizedata, dtype=intDT,count=1)[0]  # size 4 bytes
                    # self.size = self.size-4
                    print(self.size)
                    self.gotSize = True
                    needBytes = 1

                elif(self.gotSize and not self.gotCommand):
                    commandData = client.read(1)
                    command = np.frombuffer(commandData, dtype=intDT8,count=1)[0]
                    print('command',command)
                    self.gotCommand = True
                    needBytes = self.size
                
                elif(self.gotCommand and not self.gotData ):
                    if not self.size==0 : 
                        totalData = b''
                        print("data part",self.size)
                        while (len(totalData))<=self.size:
                            totalData+=client.read(self.size)
                            # print(len(totalData))
                    
                    needBytes = 1
                    self.size = 0
                    print(len(totalData))
                    self.onData.emit(totalData)
                    self.gotPreamble = False
                    self.gotSize = False
                    self.gotCommand = False
                    self.gotData = False

            else:
                # print("cont")
                continue

    def run(self):
        self.listen(self.client)

class ClientTypes(enum.Enum):
    MAIN = 100
    CAM = 101
    DEPTH_CAM = 102
    INVALID =104
    
from pyngrok import ngrok

DEFAULT_PORT = 8888


class Server(QObject):
    onStart = pyqtSignal(str,int)
    onClientConnect = pyqtSignal(ClientTypes)
    onClientDisconnect = pyqtSignal(ClientTypes)
    ID_REQ_PREAMBLE = ord('?')

    def __init__(self,readCallback,parent=None,name="TCP"):
        super(Server,self).__init__(parent=parent)
        self.tcpServer = QTcpServer(self)
        self.useNgrok = False
        self.useLocal = False
        self.readCallback = readCallback
        self.connections:list[QTcpSocket] = []
        self.connectedClientTypes:dict[ClientTypes,QTcpSocket]={}
        self.publicUrl = None
        
    
    

    def initLocal(self,ip,port):
        self.useLocal = True
        self.useNgrok = False
        if(ip==None and port==None):
            info = QHostInfo.fromName(QHostInfo.localHostName())
            self.ip = info.addresses()[-1].toString()
            self.port = 8888
        else:
            self.ip = ip
            self.port = port
        log.info("Server Init Local")
        
    
    def initNgrok(self,auth):
        self.useNgrok = True
        self.useLocal = False
        ngrok.set_auth_token(auth)
        log.info("Server Init Ngrok")



        

    def getNgrokPublicUrl(self):
        return self.tunnel.publicUrl
    
    def getIp(self):
        return self.ip

    def getPort(self):
        return self.port

    def setIp(self,ip):
        self.ip = ip
    
    def setPort(self,port):
        self.port = port
        
    def isListening(self):
        return self.tcpServer.isListening()

    def sessionOpened(self):
        log.info("Server Starting")

        if self.useLocal and not self.useNgrok:
            address = QHostAddress(self.ip)
            self.listen(address=address,port=self.port)
            
        elif self.useNgrok and not self.useLocal:
            address = QHostAddress("127.0.0.1")
            self.listen(address=address,port=DEFAULT_PORT)
            self.tunnel = ngrok.connect(DEFAULT_PORT, "tcp")
            print(self.tunnel.public_url)
            log.info("ngrok tunnel \"{}\" -> \"tcp://127.0.0.1:{}/\"".format(self.tunnel.public_url, DEFAULT_PORT))

            self.port = getPort(self.tunnel.public_url)
            self.ip = getHost(self.tunnel.public_url)

        self.onStart.emit(self.ip,int(self.port))
        log.info("Listening on "+self.ip +":"+str(self.port))

        
    
    def listen(self,address,port):
        if not self.tcpServer.listen(address, port):
            print("cant listen!")
            self.tcpServer.close()
            return
        self.tcpServer.newConnection.connect(self._handleNewConnection)

    def getClientType(self,connection:QTcpSocket):
        for type, client in self.connectedClientTypes.items():  
            if client == connection:
                return ClientTypes(type)


    def stop(self):
        if len(self.connections)>0:
            for client in self.connections:
                log.info("Disconnection "+client.peerName())
                
                client.disconnect()
                client.close()
                log.info("Client Disconnect")
                self.connections.remove(client)
                clientType = self.getClientType(connection=client)
                self.onClientDisconnect.emit(clientType)
                del self.connectedClientTypes[clientType]

        self.tcpServer.disconnect()
        self.tcpServer.close()
        log.info("Server Stop")

        if self.useNgrok and self.tunnel!=None:
            ngrok.disconnect(self.tunnel.public_url)

    def readData(self):
        for client in self.connections:
            if client.bytesAvailable() > 0:
                if client in self.connectedClientTypes.values():
                    self.readCallback(client.readAll(),self.getClientType(connection=client))
                else:
                    data = client.readAll()
                    # print(data)
                    if int.from_bytes(data[0],'big') == self.ID_REQ_PREAMBLE:
                        try:
                            print(int.from_bytes(data[1],'big'))
                            clientType = ClientTypes(int.from_bytes(data[1],'big'))
                        except ValueError:
                            clientType =  ClientTypes.INVALID
                        self.connectedClientTypes[clientType] = client
                        self.onClientConnect.emit(clientType)
                    else:
                        client.write('?'.encode('utf-8'))
                    # print(self.connectedClientTypes)


                        
                       
    def sendData(self,dataInBytes:bytes,type:ClientTypes):
        client =  self.connectedClientTypes.get(type)
        written =  client.write(dataInBytes)
        log.info("Written : {written}".format(written=written))

        if written != len(dataInBytes):
            log.info ("BidirectionalCommunication error - message not sent")
        client.flush()

    def checkClientConnection(self,clientType:ClientTypes):
        client  = self.connectedClientTypes.get(clientType,None)
        if client:
            return client.state() == QTcpSocket.SocketState.ConnectedState
        else: 
            return False

    def _handleNewConnection(self):
        newConnection:QTcpSocket = self.tcpServer.nextPendingConnection()
        log.info("Client {name} Connected from {ip}:{port}".format(name=newConnection.peerName(),ip=newConnection.peerAddress().toString(),port=newConnection.peerPort()))
        newConnection.readyRead.connect(self.readData)
        newConnection.flush()
        
        newConnection.error.connect(self._displayError)
        newConnection.disconnected.connect(lambda: self._handleDisconnect(newConnection))
        self.connections.append(newConnection)
        newConnection.write('?'.encode('utf-8'))

        
        

    def _handleDisconnect(self,client:QTcpSocket):
        
        log.info("Client {name} Disconnected from {ip}:{port}".format(name=client.peerName(),ip=client.peerAddress().toString(),port=client.peerPort()))
        client.deleteLater()
        
        self.connections.remove(client)
        clientType = self.getClientType(connection=client)
        self.onClientDisconnect.emit(clientType)
        del self.connectedClientTypes[clientType]
        



    def _displayError(self, socketError):

        if socketError == QAbstractSocket.RemoteHostClosedError:
            pass
        elif socketError == QAbstractSocket.HostNotFoundError:
            print ("The host was not found. Please check the host name and port settings.")
        elif socketError == QAbstractSocket.ConnectionRefusedError:
            print ("The connection was refused by the peer.")
        else:
            print ("The following error occurred: %s." % self.tcpSocket.errorString())


# def hi():
#     print(0)

# serv = Server(hi)
# serv.sessionOpened()
# print(QHostInfo.hostName())

# info = QHostInfo.fromName(QHostInfo.localHostName())
# print(info.addresses()[-1].toString())
# for add  in info.addresses():
#     print(add.toString())