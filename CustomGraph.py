

import numpy as np
import random
import pyqtgraph as pg
from PyQt5.QtCore import QSize, QTime, QTimer

def r(): return random.randint(0, 255)

def randColor():
    return '#{:02x}{:02x}{:02x}'.format(r(), r(), r())

def genColorCode(r,g,b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class CustomGraph(pg.GraphicsLayoutWidget):
    
    def __init__(self, parent=None, size=(10,10),legendBox=False,colors=None,name="Plot", row=None, col=None, curveNames={'hello':randColor(), 'hi':randColor()}, windowWidth=500):
        super(CustomGraph,self).__init__(parent=parent,size=size)
        self.values = [0,0,0]
        self.plotter = self.addPlot(title=name, row=row, col=col)

        # self.plotter.addLegend()
        if legendBox:
            self.l = pg.LegendItem((20, 40), offset=(70, 10),
                            pen=pg.mkPen('r'), labelTextColor='w')
        else: 
            self.l = pg.LegendItem(offset=(70, 10),labelTextColor='w')

        self.l.setParentItem(self.plotter.graphicsItem())

        self.curves = []
        for curveName,curveColor in curveNames.items():
            self.curves.append(self.plotter.plot(
                pen=pg.mkPen(curveColor), name=curveName,))

        i = 0
        for curve in curveNames:
            self.l.addItem(self.curves[i], curve)
            i = i+1

        self.timeSeries = {}
        for curve in curveNames:
            self.timeSeries[curve] = np.linspace(0, 0, windowWidth)

        self.ptr = -windowWidth

        self.timer=QTimer()


    def start(self):
        self.timer=QTimer()
        self.timer.timeout.connect(self.run)
        self.timer.start(100)

    def stop(self):
        if self.timer.isActive():
            self.timer.stop()

    
    def setValues(self, q):
        self.values = q
        

    def run(self):
        
        for curveName in self.timeSeries:
            self.timeSeries[curveName][:-1] = self.timeSeries[curveName][1:]

        i = 0
        for curveName in self.timeSeries:
            self.timeSeries[curveName][-1] = float(self.values[i])
            i = i+1

        self.ptr += 1
        i = 0
        for curveName in self.timeSeries:
            curve = self.curves[i]
            curve.setData(self.timeSeries[curveName])
            curve.setPos(self.ptr, 0)
            i = i+1
    
    def sizeHint(self):
        return QSize(500, 150)
    
    def setLegendSize(self,w,h):
        self.l.setFixedHeight(h)
        self.l.setFixedWidth(w)
    
    def setLegendOffset(self,x,y):
        self.l.setOffset((x,y))
    

