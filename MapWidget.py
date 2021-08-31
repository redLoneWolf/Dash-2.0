import os
import functools
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtWebChannel
QtCore.qInstallMessageHandler(lambda *args: None)
test = "   line_points = [ [38.893596444352134, -77.0381498336792],[38.893596444352134, -77.0349633693695] ]"

def convertPythonListToJSArray(points):
    jsArray = ""
    jsArray +='['
   
    for point in points:   
        jsArray += "[{longs},{lat}]".format(longs=point[0],lat=point[1])
        jsArray += ','
    jsArray+=']'

    return jsArray

def getLatLang(arrayObjects:QtCore.QJsonValue):
    LatLang = []
    for array in arrayObjects.toArray():
        lat = array.toObject().get('lat').toDouble()
        long = array.toObject().get('lng').toDouble()
        LatLang.append([lat,long])

    # print(LatLang)
    return LatLang


def getLangLat2(arrayObjects:QtCore.QJsonValue):
    LangLat = []
    for array in arrayObjects.toArray():
        lat = array.toArray()[0].toDouble()
        long = array.toArray()[1].toDouble()
        LangLat.append([lat,long])

    # print(LangLat)
    return LangLat



tlist = [ [38.893596444352134, -77.0381498336792],
            [38.893596444352134, -77.0349633693695],
            [38.893596444352134, -77.0381498336792],
            [38.893596444352134, -77.0381498336792]
            ]

class MapWidget(QtWidgets.QWidget):
  
    
    def __init__(self,callback):
        super(MapWidget, self).__init__()
        self.points=[[ 78.686600,10.935954]]
        self.setupUi()
        
        self.loaded = True
        self.startPos=[]
        self.latlng=[]
        self.onWaypointCallback = callback
        self.angle =0
        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect(self.drawLine)
        self.updateTimer.start(1000)

    def setupUi(self):
        # self.setFixedSize(640, 480)
        vbox = QtWidgets.QVBoxLayout()
        

        # self.label = QtWidgets.QLabel()
        # sp = QtWidgets.QSizePolicy()
        # sp.setVerticalStretch(0)
        # self.label.setSizePolicy(sp)
        # vbox.addWidget(self.label)
        self.view = QtWebEngineWidgets.QWebEngineView()
        channel = self.channel = QtWebChannel.QWebChannel()

        channel.registerObject("MainWindow", self)
        self.view.page().setWebChannel(channel)

        file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "map2.html",
        )
        self.view.setUrl(QtCore.QUrl.fromLocalFile(file))

        vbox.addWidget(self.view)
        
        self.waypointBtn = QtWidgets.QPushButton("Start Waypoint Mission")
        self.waypointBtn.setMaximumSize(150,30)
        self.waypointBtn.clicked.connect(self.onGotoWaypoint)
        vbox.insertWidget(0,self.waypointBtn)
        self.linePoints = []
        self.waypointBtn.setDisabled(True)
     
        self.setLayout(vbox)
        self.page = self.view.page()

    
    def drawLine(self):
        
        # if(len(self.points)==1):
            # page.runJavaScript("dat.geometry.coordinates.push([{lat},{long}])".format(lat=self.points[-1][0],long=self.points[-1][1]))
            # page.runJavaScript("map.getSource('route').setData(dat);")
            # page.runJavaScript("map.panTo([{lat},{long}])".format(lat=self.points[-1][0],long=self.points[-1][1]))
        
        if(len(self.points)>2):
        
            self.page.runJavaScript("angle ={}".format(self.angle))
            self.page.runJavaScript("dat.geometry.coordinates={};".format(convertPythonListToJSArray(points=self.points)))
        # page.runJavaScript("map.getSource('route').setData(dat);")
        # page.runJavaScript("map.panTo([{lat},{long}])".format(lat=self.points[-1][0],long=self.points[-1][1]))

        # self.points.append([self.points[-1][0]+0.00009,self.points[-1][1] + 0.00009])
        # print(convertPythonListToJSArray(points=points))

        
        # sc = "dat.geometry.coordinates.push([{lat},{long}])".format(lat=self.points[-1][0],long=self.points[-1][1])
        # page.runJavaScript("alert(dat.geometry.coordinates)")
        # print(sc)
        # page.runJavaScript(sc)
        
    
    def reload(self):
        self.view.reload()
        self.loaded = True


    @QtCore.pyqtSlot(float, float)
    def onMapMove(self, lat, lng):
        self.label.setText("Lng: {:.5f}, Lat: {:.5f}".format(lng, lat))
        # page = self.view.page()
        # page.runJavaScript("polyline.remove(map)")

    @QtCore.pyqtSlot(QtCore.QJsonValue)
    def onPolyLine(self,points:QtCore.QJsonValue):
        self.latlng = getLangLat2(points)
        self.waypointBtn.setDisabled(False)
        
    
    def onGotoWaypoint(self):
        self.onWaypointCallback(self.latlng)
        

    # def drawLine(self):
    #     page = self.view.page()
    #     if(len(self.points)==1):
    #         page.runJavaScript("map.setView(["+str(self.points[-1][0])+"," + str(self.points[-1][1]) + "], 25)")

    #     if(len(self.points)%50==0):
    #         # page.runJavaScript("polyline.remove(map)")
    #         # self.points.append([self.points[-1][0]+0.00009,self.points[-1][1] + 0.00009])
    #         page.runJavaScript("var line_points = "+convertPythonListToJSArray(self.points))
    #         page.runJavaScript("var polyline = L.polyline(line_points, polyline_options).addTo(map)")
            

    def updateMapLine(self,points,angle):
        self.points.append(points)
        self.angle = angle-45
        # self.drawLine()

    def clear(self):
        # self.page.runJavaScript("lavers = map.getStyle().layers;\
        # lavers.forEach(clear);")
        tes = "map.style.stylesheet.layers.forEach(function(layer) {map.removeLayer(layer.id);});"
        tes = "map.removeLayer('route');truckMarker.remove();"
        self.page.runJavaScript(tes)
        self.loaded = False

    def isNotReady(self):
        print(self.loaded)
        return self.loaded
        # with open('map.js', 'r') as f:
        #     frame = self.view.page().mainFrame()
        #     frame.evaluateJavaScript(f.read())

def hi(ji):
    print('from hi',ji)

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = MapWidget(hi)
    w.show()
    sys.exit(app.exec_())