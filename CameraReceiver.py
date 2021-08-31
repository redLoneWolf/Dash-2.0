
import sys
import os
import time
from typing import Callable
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QPoint, QRect, QSize, QThread, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QByteArray, QDataStream, QIODevice
from PyQt5.QtWidgets import QApplication, QDialog, QRubberBand,QVBoxLayout,QWidget,QPushButton,QMainWindow,QLineEdit,QMessageBox,QSizePolicy,QLabel
from PyQt5.QtNetwork import QHostAddress, QTcpServer,QTcpSocket,QAbstractSocket
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
import numpy as np
from PyQt5.QtCore import pyqtSlot
from numpy.core.fromnumeric import nonzero
import qdarkstyle
from PIL import Image,UnidentifiedImageError,ImageQt
from io import BytesIO  
import cv2 as cv
import asyncio
# import qimage2ndarray
from TCPServer import Server
# from Tracking import ProcessImage

intDT = np.dtype(np.int32).newbyteorder('>')
floatDT = np.dtype(np.float32).newbyteorder('>')
charDT= np.dtype('U1').newbyteorder('>')
intDT8 = np.dtype(np.byte).newbyteorder('>')


class FrameReceiverThread(QThread):
    PREAMBLE = ord('$')
    changePixmap = pyqtSignal(QImage)

    def __init__(self,ip ,port,parent=None):
        super().__init__(parent=parent)
        self.ip = ip
        self.port = port

    async def listen(self,reader, writer,callback):
        addr = writer.get_extra_info('peername')

        print(f"Connected DEV {addr!r}")
        while True:
            data = await reader.read(1) # preamble 1 byte
            preamble = np.frombuffer(data, dtype=intDT8,count=1)[0]
            if preamble ==self.PREAMBLE:
                lenght = np.frombuffer(await reader.read(4), dtype=intDT,count=1)[0]  # size 4 bytes
                lenght = lenght-4
                print(lenght)
                if lenght < 0 or lenght > 1228800:  # Width X Height X 4            32-bit bitmap  is 4 bytes per pixel
                    print("neg")
                    continue

                totalData = b''
                while (len(totalData))<=lenght:
                    totalData+=await reader.read(lenght)
                    print(totalData)
                    self.terminate()
                    sys.exit()

                try:
                    imageBytes =  BytesIO(bytes(totalData))
                    
                    qimg = QImage()
                    qimg.loadFromData(imageBytes.getvalue())
                    callback.emit(qimg)
                except UnidentifiedImageError as e:
                    print(e.strerror)
                    continue
            else:
                continue

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        coro = asyncio.start_server(lambda r, w: self.listen(r, w,self.changePixmap), self.ip,self.port, loop=loop)
        server = loop.run_until_complete(coro)
        print('Serving on {}'.format(server.sockets[0].getsockname()))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        # Close the server
        server.close()
        loop.run_forever(server.wait_closed())
        loop.close()


class FrameGetter(QObject):
    PREAMBLE_POS = 0
    PREAMBLE = ord('$')
    SIZE_POS = 1
    DATA_OFSET_POS = 5
    PREAMBLE_SIZE =1
    SIZE_SIZE  = 4
    COMMAND_SIZE = 1

    changePixmap = pyqtSignal(QImage)

    def __init__(self,ip ,port,name):
        super().__init__()
        self.ip = ip
        self.port = port
        self.buffer = b''
        self.name = name
        self.server = Server(readCallback=self.onData,ip=self.ip,port=self.port,name=self.name)
        self.gotPreamble = False
        self.gotSize = False
   
        self.gotData = False
        self.setObjectName("Depth")
    
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
            # print(len(self.buffer))
  

    def start(self):
        self.server.sessionOpened()

    def stop(self):
        self.server.stop()
    
    def isListening(self):
        return self.server.isListening()
        print('fr',self.server.isListening())

    def appendToReadBuffer(self,data):
        self.buffer +=data

    def clearReadBuffer(self):
        # print('clearing')
        self.buffer = b''



# class OpencvReceiverThread(QThread):
    
#     changePixmap = pyqtSignal(np.ndarray)
#     running = True
#     def __init__(self,ip ,port,tracker=None,parent=None):
#         super().__init__(parent=parent)
#         self.ip = ip
#         self.port = port
#         self.url = "http://"+self.ip+":"+str(self.port)+"/frame.jpg"
#         self.tracker = tracker
#         if tracker is None:
#             self.tracker = "CSRT"
#         print(self.url)
#         self.BB = None
#         self.trackerWindow = None
#         self.track = False
#         self.cam = cv.VideoCapture(self.url)

#     def setRunning(self,stat):
#         self.running = stat
#         self.cam.release()

#     def initTracker(self):
#         self.trackerWindow = ProcessImage(self.tracker,self.currentFrame,self.BB)
#         self.track = True

#     def isRunning(self):
#         return self.running
    
#     # def setTracker(self):

    

#     def setROI(self,roi):
#         self.BB = roi

#     def run(self):
#         while self.running:
#             success, frame = self.cam.read()
#             self.currentFrame = frame
#             # print(type(frame))
#             # cv.imshow('Input', frame)
#             # if (cv.waitKey(1)==27 & 0xFF == ord('q')):
#             #     cv.destroyAllWindows()
#             # if success:
            

#             if(self.BB is not None):
#                 self.initTracker()

#             if self.track:
#                 fr = self.trackerWindow.DetectObject(self.currentFrame)
#                 if fr is not None:
#                     frame = fr

#             self.changePixmap.emit(frame)

            
                

        




class CameraWidget(QWidget):
    def __init__(self,parent=None,ip='192.168.43.214',port=8888 ,ViewName="Camera",ROICallback=None,ImageCallBack=None):
        super(CameraWidget,self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose,False)
        self.title = 'PyQt5 Video'
        self.ip = ip
        self.port = port
        self.ROICallback = ROICallback
        self.ImageCallBack = ImageCallBack
        self.setStyleSheet(" margin:5px; border:1px solid rgb(0, 255, 0); ")

        self.name = ViewName
        self.resize(1920, 480)
        self.label = QLabel( self.name+' Here',self)
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.resize(1920, 480)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.label)
        self.frameGet = None
        self.currentFrame = None
        self.trackerWindow = None
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()

    def mousePressEvent(self, event):
    
        if event.button() == Qt.LeftButton:
        
            self.origin = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
    
    def mouseMoveEvent(self, event):
    
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
    
    def mouseReleaseEvent(self, event):
    
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
            rect = self.rubberBand.geometry()
            # print(rect)
            # cropQPixmap = self.label.pixmap().copy(rect)
            # cropQPixmap.save('cropped.png')
            if(self.ROICallback is not None):
                self.ROICallback(rect.x(),rect.y(),rect.width(),rect.height())
                # self.frameGet.setROI((rect.x(),rect.y(),rect.width(),rect.height()))
                # self.trackerWindow = ProcessImage("CSRT",self.currentFrame,(rect.x(),rect.y(),rect.width(),rect.height()))


    def start(self,ip,port,):
        self.ip = ip
        self.port = port
        # if tracker:
        #     self.frameGet = OpencvReceiverThread(self.ip,self.port,tracker)
        # else:
        #     self.frameGet = OpencvReceiverThread(self.ip,self.port)

        self.frameGet = FrameGetter(ip,port,self.name)
        self.frameGet.changePixmap.connect(self.setImage)
        self.frameGet.start()
        
        # self.frameGet.changePixmap.connect(self.onImage)
        # self.frameGet.start()

        
    def stop(self):
        if self.frameGet:
            self.frameGet.stop()


    def isListening(self):
        if self.frameGet:
            return self.frameGet.isListening()
        else:
            return False

    def resizeView(self,w,h):
        self.resize(w, h)
        self.label.resize(w, h)

    def closeEvent(self, event):
        self.frameGet.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def onImage(self,frame):

        height, width, bytesPerComponent = frame.shape
        bytesPerLine = 3 * width
        cv.cvtColor(frame, cv.COLOR_BGR2RGB, frame)   
        

        # self.ImageCallBack(frame)                                        
        QImg = QImage(frame.data, width, height, bytesPerLine,QImage.Format_RGB888)
        self.setImage(QImg)
        
    @pyqtSlot(QImage)
    def setImage(self, image:QImage):
        # print(image)
      
        
        # image = QImage()
                
        # image.loadFromData(imageBytes.getvalue())
        
        if image.isNull():
            QMessageBox.information(self, "Image Viewer", "Cannot load ")
            return
        # print("setting")
        self.label.setPixmap(QPixmap.fromImage(image.convertToFormat(QImage.Format.Format_ARGB32)))
            # return
        

       
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    ex = CameraWidget()
    # ex.startListening()
    ex.show()
    sys.exit(app.exec_())