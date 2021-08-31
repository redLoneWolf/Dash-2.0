
from PIL import Image,UnidentifiedImageError,ImageQt
from io import BytesIO  
import numpy as np
from PyQt5.QtCore import QObject, QPoint, QRect, QSize, QThread, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

intDT = np.dtype(np.int32).newbyteorder('>')
floatDT = np.dtype(np.float32).newbyteorder('>')
charDT= np.dtype('U1').newbyteorder('>')
intDT8 = np.dtype(np.byte).newbyteorder('>')

class ImageParser(QObject):
    PREAMBLE_POS = 0
    PREAMBLE = ord('$')
    SIZE_POS = 1
    DATA_OFSET_POS = 5
    PREAMBLE_SIZE =1
    SIZE_SIZE  = 4
    COMMAND_SIZE = 1

    changePixmap = pyqtSignal(QImage)

    def __init__(self,name):
        super().__init__()
        self.buffer = b''
        self.name = name
        self.gotPreamble = False
        self.gotSize = False
        self.gotData = False
        self.setObjectName(name)
    
    def appendToReadBuffer(self,data):
        self.buffer +=data

    def clearReadBuffer(self):
        # print('clearing')
        self.buffer = b''

    def onData(self,dataInBytes):
        self.appendToReadBuffer(dataInBytes)

        if (np.frombuffer(self.buffer, dtype=intDT8,count=1,offset=self.PREAMBLE_POS)[0] == self.PREAMBLE):
            self.gotPreamble = True
 
            # print('preamble',len(self.buffer))
            
        else:
            print(len(self.buffer))
            print("onNewData: intruder")
            self.clearReadBuffer()
            return

        if (self.gotPreamble and len(self.buffer) >= self.SIZE_POS + self.SIZE_SIZE):
            # print('beforesize',len(self.buffer))
            self.gotSize = True
            self.dataSize = np.frombuffer(self.buffer, dtype=intDT,offset=self.SIZE_POS,count=1)[0]
            # print('after',self.dataSize)


        if (self.gotSize and len(self.buffer) >= self.DATA_OFSET_POS + self.dataSize):
            # print(self.dataSize)
            data =  self.buffer[ self.DATA_OFSET_POS : self.DATA_OFSET_POS + self.dataSize ]
            try:
                imageBytes =  BytesIO(bytes(data))
                    
                qimg = QImage()
                
                qimg.loadFromData(imageBytes.getvalue())
 
                self.changePixmap.emit(qimg)

            except UnidentifiedImageError as e:
                    print(e.strerror)
            self.buffer = self.buffer[ self.DATA_OFSET_POS + self.dataSize : ]
            self.dataSize = 0