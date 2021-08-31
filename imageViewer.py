import sys
import os
import time
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QByteArray, QDataStream, QIODevice
from PyQt5.QtWidgets import QApplication, QDialog,QVBoxLayout,QWidget,QPushButton,QMainWindow,QLineEdit,QMessageBox,QSizePolicy,QLabel
from PyQt5.QtNetwork import QHostAddress, QTcpServer,QTcpSocket,QAbstractSocket
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
import numpy as np
from PyQt5.QtCore import pyqtSlot
import qdarkstyle
from PIL import Image,UnidentifiedImageError,ImageQt
from io import BytesIO  
# import cv2
import asyncio
import qimage2ndarray

intDT = np.dtype(np.int).newbyteorder('>')
floatDT = np.dtype(np.float32).newbyteorder('>')
charDT= np.dtype('U1').newbyteorder('>')
intDT8 = np.dtype(np.byte).newbyteorder('>')

# from PIL import ImageFile
# ImageFile.LOAD_TRUNCATED_IMAGES = True
PREAMBLE = ord('$')

async def handle_echo(reader, writer,callback):
    addr = writer.get_extra_info('peername')

    print(f"Connected DEV {addr!r}")
    while True:
        data = await reader.read(1) # preamble 1 byte
        preamble = np.frombuffer(data, dtype=intDT8,count=1)[0]
        if preamble ==PREAMBLE:
            lenght = np.frombuffer(await reader.read(4), dtype=intDT,count=1)[0]  # size 4 bytes
            lenght = lenght-4
            print(lenght)
            totalData = b''
            while (len(totalData))<=lenght:
                totalData+=await reader.read(lenght)

            try:
                pic = Image.open(BytesIO(bytes(totalData)))
                print('data',len(totalData))
                # callback.emit(ImageQt.ImageQt(pic))
                open_cv_image = np.array(pic)
                # h, w, ch = open_cv_image.shape
                # bytesPerLine = ch * w
                # convertToQtFormat = QImage(open_cv_image, w, h, bytesPerLine, QImage.Format_RGB888)
                # p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                # qimage2ndarray.array2qimage(open_cv_image).save('hi2.png')
                callback.emit(qimage2ndarray.array2qimage(open_cv_image))
                # cv2.imshow('frame',open_cv_image)
                # callback.emit(p)
                

                # if cv2.waitKey(10) & 0xFF == ord('q'):
                #         break
            except UnidentifiedImageError:
                continue
        else:
            continue
    # cv2.destroyAllWindows()

    

class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

    def run(self):
        # cap = cv2.VideoCapture(0)
        # while True:
            # ret, frame = cap.read()
            # if ret:
            #     # https://stackoverflow.com/a/55468544/6622587
            #     rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            #     h, w, ch = rgbImage.shape
            #     bytesPerLine = ch * w
            #     convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
            #     p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
            #     self.changePixmap.emit(p)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        coro = asyncio.start_server(lambda r, w: handle_echo(r, w,self.changePixmap), '192.168.43.214', 8888, loop=loop)
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
        
        

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 Video'
        self.left = 100
        self.top = 100
        self.width = 300
        self.height = 200
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.resize(1080, 720)
        # self.button = QPushButton('Not Clicked', self)
        # self.button.move(20,80)
 
        self.label = QLabel('Helo',self)
        # self.label.setBackgroundRole(QPalette.Base)
        # self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setScaledContents(True)
        self.label.resize(640, 480)
        # self.label.setVisible(True)

        

        self.th = Thread(self)
        self.th.changePixmap.connect(self.setImage)
        self.th.start()
     

        


    @pyqtSlot(QImage)
    def setImage(self, image):
        print(image)
        image.save("helloooo.png")
        if image.isNull():
                QMessageBox.information(self, "Image Viewer", "Cannot load ")
                return
        
        # self.label.repaint()
        self.label.setPixmap(QPixmap.fromImage(image))
        # self.label.adjustSize()
        # self.label.update()

    # def initUI(self):
        
        
        # cap = cv2.VideoCapture(0)
        # ret, frame = cap.read()
        # rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # convertToQtFormat = QImage(rgbImage.data, rgbImage.shape[1], rgbImage.shape[0],QImage.Format_RGB888)
        # convertToQtFormat = QPixmap.fromImage(convertToQtFormat)
        # pixmap = QPixmap(convertToQtFormat)
        # resizeImage = pixmap.scaled(640, 480, Qt.KeepAspectRatio)
        # QApplication.processEvents()
        # label.setPixmap(resizeImage)
        # th = Thread(self)
        # th.changePixmap.connect(self.setImage)
        # th.start()
        
        # self.show()
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    ex = App()
    ex.show()
    sys.exit(app.exec_())