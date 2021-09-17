
from ImageParser import ImageParser
import enum
from PyQt5.QtCore import QObject
import numpy as np
from TCPServer import ClientTypes, Server
import logging
import sys

log = logging.getLogger('hello')

from PyQt5.QtCore import QObject, QPoint, QRect, QSize, QThread, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

intDT = np.dtype(np.int).newbyteorder('>')
floatDT = np.dtype(np.float32).newbyteorder('>')
doubleDT = np.dtype(np.double).newbyteorder('>')
charDT= np.dtype('U1').newbyteorder('>')
intDT8 = np.dtype(np.byte).newbyteorder('>')

class Commands(enum.Enum):
    HANDSHAKE = 200
    TELEMETRY_DATA = 100
    START_TELEMETRY = 101
    STOP_TELEMETRY = 102
    

    START_CAM_FEED = 103
    STOP_CAM_FEED = 104
    CAM_FEED_CONFIG = 105 

    START_DEPTH_CAM_FEED = 106
    STOP_DEPTH_CAM_FEED = 107


    START_WAYPOINT = 108
    STOP_WAYPOINT = 109
    WAYPOINT_DATA = 110

    ROI = 111

    USB_CONNECT = 151
    USB_DISCONNECT = 152

    # START_EXPLORE = 107
    # STOP_EXPLORE = 108

    # FOLLOW_OBJECT = 109
    # STOP_FOLLOW_OBJECT = 110

    # TORCH = 111
    WRITE_MOTOR =153

    DISCONNECT = 202

    COMMAND_NOT_FOUND = 203



class Protocol(Server):
    PREAMBLE_POS = 0
    PREAMBLE = ord('$')
    SIZE_POS = 1
    COMMAND_POS = 5
    DATA_OFSET_POS = 6

    PREAMBLE_SIZE =1
    SIZE_SIZE  = 4
    COMMAND_SIZE = 1
    
    handshake = False
    changeCam = pyqtSignal(QImage)
    changeDepth = pyqtSignal(QImage)

    def __init__(self,packetReceiveCallback,parent=None):
        super().__init__(self.onDataReceived,parent=parent)
        log.info("Protocol Init")

        self.rxbuffer = b''
        self.txbuffer = b''        
        self.dataSize = 0
        self.currentCommand = None
        self.packetReceiveCallback = packetReceiveCallback
        self.gotPreamble = False
        self.gotSize = False
        self.gotCommand = False
        self.gotData = False

    def isCamConnected(self):
        return self.checkClientConnection(ClientTypes.CAM)
    
    def isDepthConnected(self):
        return self.checkClientConnection(ClientTypes.DEPTH_CAM)
            
    def setTelemetryCallBack(self,callback):
        self.telemetryCallback = callback

    def isHandShake(self):
        return self.handshake
    
    def onDataReceived(self,bytes:bytes,clientType:ClientTypes):

        if clientType == ClientTypes.MAIN:
            self.handleMainClient(bytes=bytes)
        elif clientType == ClientTypes.CAM:
            self.CamFeedParser.onData(bytes)
        elif clientType == ClientTypes.DEPTH_CAM:
            self.DepthFeedParser.onData(bytes)


    def handleMainClient(self,bytes:bytes):
        self.appendToReadBuffer(bytes)
      
        if (np.frombuffer(self.rxbuffer, dtype=intDT8,count=1,offset=self.PREAMBLE_POS)[0] == self.PREAMBLE):
            self.gotPreamble = True
            # print('preamble')
            
        else:
            log.info("intruder")
            # print(self.rxbuffer)
            self.clearReadBuffer()
            return

        if (self.gotPreamble and len(self.rxbuffer) >= self.SIZE_POS + self.SIZE_SIZE):
            # print('beforesize',len(self.rxbuffer))
            self.gotSize = True
            self.dataSize = np.frombuffer(self.rxbuffer, dtype=intDT,offset=self.SIZE_POS,count=1)[0]
            # print('size',self.dataSize)

        if(self.gotSize and len(self.rxbuffer) >= self.COMMAND_POS + self.COMMAND_SIZE):
            self.gotCommand = True
            commandValue = np.frombuffer(self.rxbuffer, dtype=intDT8,offset=self.COMMAND_POS,count=1)[0]
            # print('comm',commandValue)
            try:
                self.currentCommand =  Commands(commandValue)
            
            except ValueError as e:
                self.currentCommand = Commands.COMMAND_NOT_FOUND
           
        if (self.gotCommand and len(self.rxbuffer) >= self.DATA_OFSET_POS + self.dataSize):
            # byteBuffer.position(3);
            # byte[] data = new byte[size];
            # byteBuffer.get(data, 0, size);
            # getUsbListener().onDataReceived(currentCommand,data);
            # dat = np.frombuffer(self.rxbuffer, dtype=floatDT,offset=self.DATA_OFSET_POS,count=self.dataSize//4)
            # print('data',dat)
            # print('datalen',len(dat))
            # if(len(dat)==3):
            #     self.telemetryCallback(dat[0],dat[1],dat[2])
            self.onCommand()
            self.dataSize = 0
            self.clearReadBuffer()

    

    def clearReadBuffer(self):
        self.rxbuffer = b''

    def appendToReadBuffer(self,data):
        self.rxbuffer +=data

    def getBuffer(self):
        return self.rxbuffer

    def setBuffer(self,newBuffer:bytearray):
        self.rxbuffer = newBuffer
    
    def getBufferLength(self):
        return len(self.rxbuffer)

    def checkPreamble(self):
        preamble = np.frombuffer(self.rxbuffer, dtype=intDT8,count=1,offset=self.PREAMBLE_POS)[0]
        print('premble ',preamble)
        if (preamble == self.PREAMBLE):
            return True
        else:
            return False
    
    def checkSize(self):
        self.dataSize = np.frombuffer(self.rxbuffer, dtype=intDT,offset=self.SIZE_POS,count=1)[0]
        # print('size ',self.dataSize)
        return self.dataSize > 0

    
    def checkCommand(self):
        commandValue = np.frombuffer(self.rxbuffer, dtype=intDT8,offset=self.COMMAND_POS,count=1)[0]
        # print('comand ',commandValue)
        try:
            self.currentCommand =  Commands(commandValue)
            
        except ValueError as e:
            self.currentCommand = Commands.COMMAND_NOT_FOUND

        # if(self.currentCommand == Commands.HANDSHAKE):
        #     self.handshake = True
        #     return

    def getDataPart(self):
        data = self.rxbuffer[ self.DATA_OFSET_POS : self.DATA_OFSET_POS + self.dataSize ]
        return data

    def getInfo(self):
        self.checkPreamble()
        self.checkSize()
        self.checkCommand()
        data = self.rxbuffer[ self.DATA_OFSET_POS : self.DATA_OFSET_POS + self.dataSize ]
        # print('info',len(data))
        # self.packetReceiveCallback(self.currentCommand,data)
    
    def addPreamble(self):
        temp = np.array(self.PREAMBLE,dtype=intDT8)
        self.txbuffer =  temp.tobytes()
    
    def addSize(self,size):
        temp = np.array(size,dtype=intDT)
        self.txbuffer +=  temp.tobytes()
    
    def addCommand(self,command):
        temp = np.array(command.value & 0xFF,dtype=intDT8)
        self.txbuffer +=  temp.tobytes()
    
    def addData(self,data):
        self.txbuffer +=  data

    def FloatToBytes(self,data):
        return np.array(data,dtype=floatDT).tobytes()
    
    def IntToBytes(self,data):
        return np.array(data,dtype=intDT).tobytes()

    def DoubleToBytes(self,data):
        return np.array(data,dtype=doubleDT).tobytes()
    
    def getAsPacket(self,command,data):          # do not change order
        self.addPreamble()
        self.addSize(len(data))
        self.addCommand(command)
        self.addData(data)
        # print(self.txbuffer)
        return self.txbuffer
    
    def sendPacket(self,command,data=b''):
        log.info("Sending : " + str(command.value) + "with "+str(len(data))+" bytes")
        serializedData = self.getAsPacket(command=command,data=data)
        super().sendData(serializedData,ClientTypes.MAIN)
        self.txbuffer = b''  

    def act(self):
        self.checkPreamble()
        self.checkSize()
        self.checkCommand()
        self.onCommand()

    def onHandShake(self):
        self.handshake = True

    def sendDisconnect(self):
        self.sendPacket(Commands.DISCONNECT)
        
    
    def connectUSB(self):
        self.sendPacket(Commands.USB_CONNECT)

    def disconnectUSB(self):
        self.sendPacket(Commands.USB_DISCONNECT)

    def startTelemetry(self):
        self.sendPacket(Commands.START_TELEMETRY)
        
    
    def stopTelemetry(self):
        self.sendPacket(Commands.STOP_TELEMETRY)

    def startCamFeed(self):
        self.sendPacket(Commands.START_CAM_FEED,self.IntToBytes([640,480]))
        self.CamFeedParser = ImageParser("RGB")
        self.CamFeedParser.changePixmap = self.changeCam
    
    def stopCamFeed(self):
        self.sendPacket(Commands.STOP_CAM_FEED)

    def startDepthFeed(self):
        self.sendPacket(Commands.START_DEPTH_CAM_FEED)
        self.DepthFeedParser = ImageParser("DEPTH")
        self.DepthFeedParser.changePixmap = self.changeDepth
    
    def stopDepthFeed(self):
        self.sendPacket(Commands.STOP_DEPTH_CAM_FEED)
    
    def startWayPoint(self,latlongs):
        self.sendPacket(Commands.START_WAYPOINT,self.DoubleToBytes(latlongs))

    def stopWayPoint(self):
        self.sendPacket(Commands.STOP_WAYPOINT)

    def sendROI(self,x,y,width,height,tracker):
        self.sendPacket(Commands.ROI,self.IntToBytes([x,y,width,height,tracker]))

    def onTelemetry(self):
        # data = self.getDataPart()
        # print('tele',len(data))
        sensordata = np.frombuffer(self.rxbuffer, dtype=floatDT,offset=self.DATA_OFSET_POS,count=12)

        locData = np.frombuffer(self.rxbuffer, dtype=doubleDT,offset=self.DATA_OFSET_POS+(4*12),count=1)
        
        n = 3
        splittedSensorData = [sensordata[i * n:(i + 1) * n] for i in range((len(sensordata) + n - 1) // n )]
        # print(self.rxbuffer[self.DATA_OFSET_POS+(4*12)+(8*1)])
        devicestats = np.frombuffer(self.rxbuffer, dtype=intDT,offset=self.DATA_OFSET_POS+(4*12)+(8*1),count=1)
  
        self.telemetryCallback(splittedSensorData,locData,devicestats)
        # print('sensor',sensordata)
        # print('loc',locData)
    
    def sendRCData(self,array):
        self.sendPacket(Commands.WRITE_MOTOR,self.IntToBytes(array))

    def onCommand(self):
        switcher = {Commands.TELEMETRY_DATA:self.onTelemetry,}
        fun = switcher.get(self.currentCommand)
        
        if fun:
            fun()

        
    
