import sys
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import *



# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2011-2013 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License along with
#  this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
Attitude indicator widget.
"""
# __author__ = 'Bitcraze AB'
class AttitudeIndicator(QWidget):
    """Widget for showing attitude"""



    def __init__(self, hz=30):
        super(AttitudeIndicator, self).__init__()

        self.roll = 0
        self.pitch = 0
        self.needUpdate = True


        self.msg = ""
        self.hz = hz

        # self.setMinimumSize(150, 150)

 
        self.updateTimer = QtCore.QTimer(self)
        

        self.msgRemove = 0

    def start(self):
        self.updateTimer=QtCore.QTimer()
        self.updateTimer.timeout.connect(self.updateAI)
        self.updateTimer.start(100)

    def stop(self):
        if self.updateTimer.isActive():
            self.updateTimer.stop()

    def updateAI(self):
        if self.msgRemove>0:
            self.msgRemove -= 1
            if self.msgRemove <= 0:
                self.msg = ""
                self.needUpdate = True


        if self.isVisible() and self.needUpdate:
            self.needUpdate = False
            self.repaint()

    def setRoll(self, roll):
        self.roll = roll
        self.needUpdate = True

    def setPitch(self, pitch):
        self.pitch = pitch
        self.needUpdate = True
        


    def setRollPitch(self, roll, pitch):
        self.roll = roll
        self.pitch = pitch
        self.needUpdate = True

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()






    def drawWidget(self, qp):
        size = self.size()
        w = size.width()
        h = size.height()

        blue = QtGui.QColor(min(255,0), min(255,61),144,  255)
        maroon = QtGui.QColor(min(255,59), min(255,41), 39,  255)

        qp.translate(w / 2, h / 2)
        qp.rotate(self.roll)
        qp.translate(0, (self.pitch * h) / 50)
        qp.translate(-w / 2, -h / 2)
        qp.setRenderHint(qp.Antialiasing)

        font = QtGui.QFont('Serif', 7, QtGui.QFont.Light)
        qp.setFont(font)

        #Draw the blue
        qp.setPen(blue)
        qp.setBrush(blue)
        qp.drawRect(-w, h/2, 3*w, -3*h)

        #Draw the maroon
        qp.setPen(maroon)
        qp.setBrush(maroon)
        qp.drawRect(-w, h/2, 3*w, 3*h)

        pen = QtGui.QPen(QtGui.QColor(255, 255, 255), 1.5,
            QtCore.Qt.SolidLine)
        qp.setPen(pen)
        qp.drawLine(-w, h / 2, 3 * w, h / 2)

        # Drawing pitch lines
        for ofset in [-180, 0, 180]:
            for i in range(-900, 900, 25):
                pos = (((i / 10.0) + 25 + ofset) * h / 50.0)
                if i % 100 == 0:
                    length = 0.35 * w
                    if i != 0:
                        if ofset == 0:
                            qp.drawText((w / 2) + (length / 2) + (w * 0.06),
                                        pos, "{}".format(-i / 10))
                            qp.drawText((w / 2) - (length / 2) - (w * 0.08),
                                        pos, "{}".format(-i / 10))
                        else:
                            qp.drawText((w / 2) + (length / 2) + (w * 0.06),
                                        pos, "{}".format(i / 10))
                            qp.drawText((w / 2) - (length / 2) - (w * 0.08),
                                        pos, "{}".format(i / 10))
                elif i % 50 == 0:
                    length = 0.2 * w
                else:
                    length = 0.1 * w

                qp.drawLine((w / 2) - (length / 2), pos,
                            (w / 2) + (length / 2), pos)

        qp.setWorldMatrixEnabled(False)

        pen = QtGui.QPen(QtGui.QColor(0, 0, 0), 2,
            QtCore.Qt.SolidLine)
        qp.setBrush(QtGui.QColor(0, 0, 0))
        qp.setPen(pen)
        qp.drawLine(0, h / 2, w, h / 2)
        


        qp.resetTransform()

        r = min(w,h)
    
        center = QtCore.QPoint(w/2, h/2)
        qp.setBrush(QtGui.QColor(0, 0, 0, 0))
        pen = QtGui.QPen(self.palette().brush(QtGui.QPalette.Window), 2, QtCore.Qt.SolidLine)
        qp.setPen(pen)
        qp.drawEllipse(center, r/2, r/2)
        pen = QtGui.QPen(QtGui.QColor("#F5F5F5"), 2, QtCore.Qt.SolidLine) # Backgorund color
        # pen = QtGui.QPen(QtGui.QColor(25,35,45), 2, QtCore.Qt.SolidLine)
        qp.setPen(pen)
        for i in range(1, max(w,h)-r//2):
            qp.drawEllipse(center, r/2+i, r/2+i)


if __name__ == "__main__":
    class Example(QWidget):

        def __init__(self):
            super(Example, self).__init__()

            self.initUI()

        def updatePitch(self, pitch):
            self.wid.setPitch(pitch - 90)

        def updateRoll(self, roll):
            self.wid.setRoll((roll / 10.0) - 180.0)
        
        
        # def updateTarget(self, target):
        #     self.wid.setHover(500+target/10.)
        # def updateBaro(self, asl):
        #     self.wid.setBaro(500+asl/10.)           
        
        
        def initUI(self):

            vbox = QVBoxLayout()

            sld = QSlider(Qt.Horizontal, self)
            sld.setFocusPolicy(Qt.NoFocus)
            sld.setRange(0, 3600)
            sld.setValue(1800)
            vbox.addWidget(sld)
            
            
            self.wid = AttitudeIndicator()
            self.wid.setMinimumSize(240, 240)
            self.wid.setMaximumSize(240, 240)

            sld.valueChanged[int].connect(self.updateRoll)
            vbox.addWidget(self.wid)

            hbox = QHBoxLayout()
            hbox.addLayout(vbox)

            sldPitch = QSlider(QtCore.Qt.Vertical, self)
            sldPitch.setFocusPolicy(QtCore.Qt.NoFocus)
            sldPitch.setRange(0, 180)
            sldPitch.setValue(90)
            sldPitch.valueChanged[int].connect(self.updatePitch)
            hbox.addWidget(sldPitch)
            
            # sldASL = QSlider(QtCore.Qt.Vertical, self)
            # sldASL.setFocusPolicy(QtCore.Qt.NoFocus)
            # sldASL.setRange(-200, 200)
            # sldASL.setValue(0)
            # sldASL.valueChanged[int].connect(self.updateBaro)
            
            # sldT = QSlider(QtCore.Qt.Vertical, self)
            # sldT.setFocusPolicy(QtCore.Qt.NoFocus)
            # sldT.setRange(-200, 200)
            # sldT.setValue(0)
            # sldT.valueChanged[int].connect(self.updateTarget)
            
            # hbox.addWidget(sldT)  
            # hbox.addWidget(sldASL)
                      

            self.setLayout(hbox)

            self.setGeometry(50, 50, 510, 510)
            self.setWindowTitle('Attitude Indicator')
            self.show()

    def main():

        app = QApplication(sys.argv)
        ex = Example()
        sys.exit(app.exec_())


    if __name__ == '__main__':
        main()