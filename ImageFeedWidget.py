
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


class ImageFeedWidget(QWidget):
    def __init__(self,name,parent=None):
        super(ImageFeedWidget,self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose,False)
        self.title = name
        self.setStyleSheet(" margin:5px; border:1px solid rgb(0, 255, 0); ")
        self.name = name
        self.resize(1920, 480)
        self.label = QLabel( self.name+' Here',self)
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.resize(1920, 480)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.label)


    def resizeView(self,w,h):
        self.resize(w, h)
        self.label.resize(w, h)

    def closeEvent(self, event):
        event.accept()

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
    ex = ImageFeedWidget()
    # ex.startListening()
    ex.show()
    sys.exit(app.exec_())