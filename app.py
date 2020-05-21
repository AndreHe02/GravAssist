
import sys
#from PySide2.QtWidgets import *
from PySide2.QtWidgets import QApplication, QMainWindow, QAction, QSplashScreen, QSplitter, QLineEdit, QGridLayout, QWidget, QPushButton, QMessageBox
from PySide2.QtWidgets import QCalendarWidget, QTreeWidget, QStackedWidget, QLabel, QVBoxLayout, QSizePolicy, QComboBox, QSlider, QTreeWidgetItem
from PySide2.QtOpenGL import QGLWidget
from PySide2.QtCore import Slot, QFile, QTimer, Qt, QDate
from PySide2.QtGui import QKeySequence, QIcon, QPixmap

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from datetime import datetime, timedelta
from src.SPICE.ephemeris import ephemeris
from src.traj import trajectory
from src.path_search import *
import spiceypy as sp
import numpy as np
import os

import src.visualizeGL as vis
#
# data related
#
viewTime = datetime(2001,1,1)
#
# graphic related
#
#list of everything that will be drawn
drawables = []
defaultTrajColor = [130, 184, 97]
trajColors = [[255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255]]

framerate = 30.0

class path(object):

    def __init__(self, launchTime, deltaV, duration, entranceTimes, trajectories):
        #this is just for demo
        self.launch = launchTime

        #other basic info for display
        self.deltaV = deltaV

        #in timedelta form
        self.duration = duration

        #a list of times on which the probe enters a trajectory,
        #the length of this array should match that of the length of trajectories
        self.entranceTimes = entranceTimes
        self.trajectories = trajectories

        self.flyby = []
        for i in self.trajectories:
            self.flyby.append(i.body.name)

    #what absolute position is the probe at 'time'
    def getPosition(self, flightTime):
        t = self.getTrajTime(flightTime)
        traj = self.getTrajectory(flightTime)

        area = traj.av * t
        absTime = self.launch+timedelta(seconds=flightTime)
        #print('t: ', self.launch+timedelta(seconds=flightTime))
        #print('tName: ', type(absTime).__name__)
        return np.array(traj.body.state(absTime)[0:3]) + np.array(sp.prop2b(traj.GM, traj.entranceState, t)[0:3])

    def getRelPosition(self, flightTime):
        t = self.getTrajTime(flightTime)
        traj = self.getTrajectory(flightTime)

        area = traj.av * t
        absTime = self.launch+timedelta(seconds=flightTime)
        #print('t: ', self.launch+timedelta(seconds=flightTime))
        #print('tName: ', type(absTime).__name__)
        return np.array(sp.prop2b(traj.GM, traj.entranceState, t)[0:3])

    #what trajectory is the probe in at 'time'
    def getTrajectory(self, flightTime):
        for i, e in reversed(list(enumerate(self.entranceTimes))):
            if flightTime >= (e - self.launch).total_seconds():
                return self.trajectories[i]

    #time in orbit
    def getTrajTime(self, flightTime):
        for i, e in reversed(list(enumerate(self.entranceTimes))):
            if flightTime >= (e - self.launch).total_seconds():
                return flightTime - (e-self.launch).total_seconds()

def calculatePath(departure, arrival, earliest, latest, sun):

    #loading message box
    loading = QMessageBox()
    loading.setText('calculating path')
    loading.setIcon(QMessageBox.Information)
    loading.setStandardButtons()
    loading.exec_()

    #just for demo purposes, the real thing should end up in a list
    tsf, DV, t0, T = opt_transfer(departure, arrival, earliest, latest, sun.Gmass[0] )
    tsf_path = path( t0, DV, T, [t0], [trajectory(sun, t0, np.concatenate((departure.state(t0)[:3], tsf['v1'])))] )

    #close loading message box
    loading.done(0)

    return [tsf_path]

class Mouse(object):

    def __init__(self):
        self.pos = [0,0]
        self.draggingIn = None
mouse = Mouse()

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Grav Assist Simulator")

        # Status Bar
        self.status = self.statusBar()
        self.status.showMessage("sample status bar message")

        # Window dimensions
        geometry = QApplication.desktop().availableGeometry(self)
        if geometry.width() > 1024 and geometry.height() > 720:
            self.setGeometry(50,50,1024,720)

        tbox = Toolbox()
        gl1 = glWidget()
        gl2 = glWidget()

        self.splitter = cntrView(gl1, tbox)
        self.player = plyrView(gl2)

        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.splitter)
        self.stacked.addWidget(self.player)

        self.setCentralWidget(self.stacked)

        self.useSplitter()

    def useSplitter(self):
        self.stacked.setCurrentWidget(self.splitter)

    def usePlayer(self):
        global selectedSolution
        if selectedSolution == None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("You need to choose a particular solution!")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
        else:
            self.player.notifyChange()
            self.stacked.setCurrentWidget(self.player)

class cntrView(QSplitter):

    def __init__(self, graph, toolbox):
        QSplitter.__init__(self, Qt.Horizontal)

        #prepare graph
        self.graphWidget = graph
        self.addWidget(graph)

        #add toolbox on the right
        self.tBox = toolbox
        self.addWidget(self.tBox)

    def mousePressEvent(self, e):
        global mouse
        clicked = self.childAt(mouse.pos[0], mouse.pos[1])
        mouse.pos = [e.x(), e.y()]

        if e.button() == Qt.MouseButton.LeftButton:
            if clicked == self.graphWidget:
                self.graphWidget.setFocus()
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_LEFT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])
            elif clicked == self.tBox:
                mouse.draggingIn = None
                self.tBox.setFocus()
            else:
                mouse.draggingIn = None
        elif e.button() == Qt.MouseButton.RightButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_RIGHT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])
            else:
                mouse.draggingIn = None

    def mouseReleaseEvent(self, e):
        global mouse
        clicked = self.childAt(mouse.pos[0], mouse.pos[1])
        mouse.pos = [e.x(), e.y()]

        if e.button() == Qt.MouseButton.LeftButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = None
                self.graphWidget.mClick(GLUT_LEFT_BUTTON, GLUT_UP, mouse.pos[0], mouse.pos[1])
        elif e.button() == Qt.MouseButton.RightButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = None
                self.graphWidget.mClick(GLUT_RIGHT_BUTTON, GLUT_UP, mouse.pos[0], mouse.pos[1])

    def mouseMoveEvent(self, e):
        #print(e)
        mouse.pos = [e.x(), e.y()]
        if self.childAt(mouse.pos[0], mouse.pos[1]) == self.graphWidget:
            self.graphWidget.mDrag(mouse.pos[0], mouse.pos[1])

    def keyPressEvent(self, e):
        pass
        """
        if e.key() == Qt.Key_Escape:
            self.parent().close()
        else:
            self.graphWidget.kPress(e.key())"""

class Toolbox(QWidget):
    def __init__(self):
        QWidget.__init__(self, None)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.content = []

        #label
        l1 = QLabel()
        l1.setText("earliest departure")
        l1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #l1.setFixedHeight(30)
        self.layout.addWidget(l1, 0, 0)
        #calendar1
        calendar1 = QCalendarWidget()
        calendar1.setGridVisible(True)
        calendar1.setHorizontalHeaderFormat(QCalendarWidget.NoHorizontalHeader)
        calendar1.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar1.setFixedSize(200,200)
        #calendar1.clicked.connect(self.showDate)
        self.calendar1 = calendar1
        self.layout.addWidget(calendar1, 1, 0)
        #label
        l2 = QLabel()
        l2.setText("latest arrival")
        l2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #l2.setFixedHeight(30)
        self.layout.addWidget(l2, 0, 1)
        #calendar2
        calendar2 = QCalendarWidget()
        calendar2.setGridVisible(True)
        calendar2.setHorizontalHeaderFormat(QCalendarWidget.NoHorizontalHeader)
        calendar2.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar2.setFixedSize(200,200)
        #calendar2.clicked.connect(self.showDate)
        self.calendar2 = calendar2
        self.layout.addWidget(calendar2, 1, 1)

        l3 = QLabel()
        l3.setText('departure from')
        self.layout.addWidget(l3, 2, 0)

        #departure selector
        self.departure = QComboBox()
        self.departure.addItems(['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'])
        self.layout.addWidget(self.departure, 2, 1)

        l4 = QLabel()
        l4.setText('arrive at')
        self.layout.addWidget(l4, 3, 0)

        #arrival selector
        self.arrival = QComboBox()
        self.arrival.addItems(['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'])
        self.layout.addWidget(self.arrival, 3, 1)

        #calculate button
        self.calculate = QPushButton('calculate path', self)
        self.calculate.clicked.connect(self.report)
        self.layout.addWidget(self.calculate, 4, 0, rowSpan = 1, columnSpan = 2)

        #list of solutions
        l5 = QLabel()
        l5.setText('available paths')
        self.layout.addWidget(l5, 5, 0)
        self.solutions = QTreeWidget()
        hd = QTreeWidgetItem()
        self.solutions.setHeaderLabels(['launch','deltaV (km/s)', 'duration (yr)', 'flyby'])

        self.layout.addWidget(self.solutions, 6, 0, 1, 2)

        global selectedSolution
        selectedSolution = None

        #animate button
        self.animate = QPushButton('view animated', self)
        self.animate.clicked.connect(self.anim)
        self.layout.addWidget(self.animate, 7, 0, rowSpan = 1, columnSpan = 2)

    def report(self):
        earliest = self.calendar1.selectedDate().toPython()
        earliest = datetime.combine(earliest, datetime.min.time()) #convert date to datetime

        latest = self.calendar2.selectedDate().toPython()
        latest = datetime.combine(latest, datetime.min.time())
        if earliest >= latest:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText('latest departure should come after earliest departure')
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            return
        depart = self.departure.currentText()
        arrive = self.arrival.currentText()
        if depart == arrive:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText('departure must be different from arrival')
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            return
        print('calculate the optimal path from', depart,' to ', arrive, ' that starts after', earliest,' and arrives before', latest)

        #calculation
        global results
        results = calculatePath(ephem.get_body(depart.upper()), ephem.get_body(arrive.upper()), earliest, latest, ephem.get_body('SUN'))
        #update solutions list
        self.solutions.clear()
        for i in results:
            iItem = QTreeWidgetItem([
                i.launch.strftime('%Y.%m.%d'),
                str(i.deltaV),
                str(i.duration.total_seconds()/ 31556952),
                ', '.join(i.flyby)
            ])
            self.solutions.addTopLevelItem(iItem)

    def anim(self):
        global results
        global selectedSolution

        selectedSolution = results[self.solutions.indexFromItem(self.solutions.currentItem()).row()]

        global window
        window.usePlayer()

        """
        global gl
        global viewTime
        s = self.calendar1.selectedDate().toPython()
        f = self.calendar2.selectedDate().toPython()
        print(s, f)
        if s < f:
            viewTime = s
            gl.animate(self.calendar2.selectedDate().toPython())"""


class plyrView(QWidget):
    def __init__(self, graph):
        QWidget.__init__(self, None)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        #animate button
        self.back = QPushButton('back', self)
        self.back.setToolTip('go back to input page')
        self.back.clicked.connect(self.switch)
        self.layout.addWidget(self.back, 0, 0)

        #screen
        self.graphWidget = graph
        self.layout.addWidget(graph, 1, 0, 1, 8)
        self.graphWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        #progress slider
        self.progress = QSlider(Qt.Horizontal)
        self.progress.sliderPressed.connect(self.progressPrs)
        self.progress.sliderReleased.connect(self.progressRls)
        self.layout.addWidget(self.progress, 2, 1, 2, 1)

        #play/pause button
        self.isPlaying = False
        self.wasPlaying = False
        self.play = QPushButton('\u25B6', self)
        self.play.setToolTip('play/pause')
        self.play.clicked.connect(self.playBtn)
        self.play.setStyleSheet('QPushButton {font-weight: bold;}')
        self.layout.addWidget(self.play, 2, 0, 2, 1)

        #speed button
        spdLbl = QLabel()
        spdLbl.setText("video speed: ")
        spdLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.layout.addWidget(spdLbl, 2, 2)
        self.speed = QPushButton('7 days/second')
        self.speed.setToolTip('change playing speed')
        self.speed.clicked.connect(self.changeSpd)
        self.layout.addWidget(self.speed, 3, 2)
        self.vidSpeed = 604800 # in seconds per second

        #view mode button
        mdLbl = QLabel()
        mdLbl.setText('camera mode')
        self.layout.addWidget(mdLbl, 2, 3)
        self.mode = QComboBox()
        self.mode.addItems(['chase','bird\'s eye','flyby'])
        self.mode.currentIndexChanged.connect(self.setMode)
        self.vidMode = 0
        self.layout.addWidget(self.mode, 3, 3)

        #info button
        self.info = QPushButton('info')
        self.info.setToolTip('show info about path')
        self.info.clicked.connect(self.showInfo)
        self.layout.addWidget(self.info, 3, 4)

    def notifyChange(self):
        global selectedSolution
        ss = selectedSolution

        self.progress.setMinimum(0)
        self.progress.setMaximum(ss.duration.total_seconds())


    def playBtn(self):
        if self.isPlaying == True:
            self.wasPlaying = False
            self.pauseVid()
        else:
            self.wasPlaying = True
            self.playVid()

    def recurDraw(self):
        if self.isPlaying:
            global viewTime
            global selectedSolution
            viewTime = selectedSolution.launch + timedelta(seconds=self.progress.value())

            global framerate
            dT = timedelta(seconds = self.vidSpeed / framerate)
            viewTime = viewTime + dT
            self.progress.setValue(round((viewTime-selectedSolution.launch).total_seconds()))

            QTimer.singleShot(round(1000 / framerate), self.recurDraw)

            self.updateCam()
            self.graphWidget.updateGL()

    def updateCam(self):
        global selectedSolution, viewTime
        deltaT = (viewTime - selectedSolution.launch).total_seconds()
        #chase
        if self.vidMode == 0:
            vis.autoChase(selectedSolution.getPosition(deltaT))

        #flyby
        elif self.vidMode == 2:
            body = selectedSolution.getTrajectory(deltaT).body
            if not body.name == 'SUN':
                vis.autoFlyby(body.state(viewTime), body.soi(viewTime))
            else:
                vis.autoSolarCenter()

        #bird eye
        elif self.vidMode == 1:
            global solarSystemPlaneUP
            vis.autoBirdEye(solarSystemPlaneUP, selectedSolution.getTrajectory(deltaT).body.state(viewTime))


    def playVid(self):
        #print('playing')
        self.play.setText('\u2759\u2759')
        self.play.hide()
        self.play.show()
        self.isPlaying = True

        self.recurDraw()

    def pauseVid(self):
        #print('pausing')
        self.play.setText('\u25B6')
        self.play.hide()
        self.play.show()
        self.isPlaying = False

    def progressPrs(self):
        if self.isPlaying:
            self.pauseVid()
    def progressRls(self):
        if self.wasPlaying:
            self.playVid()

    def changeSpd(self):
        if self.isPlaying:
            self.pauseVid()

        if self.vidSpeed==1 * 86400:
            self.vidSpeed = 7 * 86400
            self.speed.setText('7 days/second')
        elif self.vidSpeed == 7 * 86400:
            self.vidSpeed = 30 * 86400
            self.speed.setText('30 days/second')
        elif self.vidSpeed == 30 * 86400:
            self.vidSpeed = 100 * 86400
            self.speed.setText('100 days/second')
        elif self.vidSpeed == 100 * 86400:
            self.vidSpeed = 1 * 86400
            self.speed.setText('1 day/second')

        self.speed.hide()
        self.speed.show()

        if self.wasPlaying:
            self.playVid()

    def setMode(self):
        if self.isPlaying:
            self.pauseVid()
        print(self.mode.currentText(), self.mode.currentIndex())
        self.vidMode = self.mode.currentIndex()

        if self.wasPlaying:
            self.playVid()

    def showInfo(self):
        if self.isPlaying:
            self.pauseVid()
        #show info here
            #apejfaioejfaper
        if self.wasPlaying:
            self.playVid()

    def switch(self):
        global window
        window.useSplitter()

    def mousePressEvent(self, e):
        global mouse
        clicked = self.childAt(mouse.pos[0], mouse.pos[1])
        mouse.pos = [e.x(), e.y()]

        if e.button() == Qt.MouseButton.LeftButton:
            if clicked == self.graphWidget:
                self.graphWidget.setFocus()
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_LEFT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])

                if self.isPlaying:
                    self.pauseVid()
            else:
                mouse.draggingIn = None
        elif e.button() == Qt.MouseButton.RightButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_RIGHT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])

                if self.isPlaying:
                    self.pauseVid()
            else:
                mouse.draggingIn = None

    def mouseReleaseEvent(self, e):
        global mouse
        clicked = self.childAt(mouse.pos[0], mouse.pos[1])
        mouse.pos = [e.x(), e.y()]

        if e.button() == Qt.MouseButton.LeftButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = None
                self.graphWidget.mClick(GLUT_LEFT_BUTTON, GLUT_UP, mouse.pos[0], mouse.pos[1])

                if self.wasPlaying == True:
                    self.playVid()
        elif e.button() == Qt.MouseButton.RightButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = None
                self.graphWidget.mClick(GLUT_RIGHT_BUTTON, GLUT_UP, mouse.pos[0], mouse.pos[1])

                if self.wasPlaying == True:
                    self.playVid()
    def mouseMoveEvent(self, e):
        #print(e)
        mouse.pos = [e.x(), e.y()]
        if self.childAt(mouse.pos[0], mouse.pos[1]) == self.graphWidget:
            self.graphWidget.mDrag(mouse.pos[0], mouse.pos[1])

    def keyPressEvent(self, e):
        pass
        """
        if e.key() == Qt.Key_Escape:
            self.parent().close()
        else:
            self.graphWidget.kPress(e.key())"""

class glWidget(QGLWidget):

    def __init__(self):
        QGLWidget.__init__(self, None)
        self.setMinimumSize(640, 480)
        self.makeCurrent()
        self.initted = False
        self.initializeGL()
        self.solution = None

    def setSolution(self, solution):
        self.solution = solution

    def paintGL(self):
        global drawables
        global window
        window.status.showMessage("drawing")

        global viewTime

        #all the planets
        for i in vis.planets:
            if i == 'SUN':
                up = [0,0,1]
                traj = None
            else:
                #up = np.cross(vis.planets[i].body.state(viewTime)[0:3], vis.planets[i].body.state(viewTime)[4:6])
                #up /= np.linalg.norm(up)
                global ephem
                traj = trajectory(vis.planets['SUN'].body, viewTime, vis.planets[i].body.state(viewTime))
                up = traj.up

                global defaultTrajColor
                #color, foc, ecc, matrix, a, angleIn=0, angleOut=0
                trajDraw = vis.orbit(defaultTrajColor, [0,0,0], traj.rMtrx, traj.elements['A'], traj.elements['ECC'])
                drawables.append(vis.drawable(trajDraw))

            #                                                      position                 upwards direction
            drawables.append(vis.drawable(vis.planets[i], vis.planets[i].body.state(viewTime)[0:3], up))

        #all other trajectories
        global selectedSolution
        if not selectedSolution == None:
            index = 0
            global trajColors
            for i in selectedSolution.trajectories:
                iOrbit = vis.orbit(trajColors[index], i.body.state(viewTime)[0:3], i.rMtrx, i.elements['A'], i.elements['ECC'], i.angleIn, i.angleOut)
                drawables.append(vis.drawable(iOrbit))
            deltaT = (viewTime - selectedSolution.launch).total_seconds()
            """print("t = ", deltaT, "s, at ", selectedSolution.getPosition(deltaT), " on orbit around ", selectedSolution.getTrajectory(deltaT).body.name)
            """#print('------')

        vis.draw(drawables)
        drawables = []

        window.status.showMessage("solar system at: "+viewTime.strftime("%Y-%m-%d"))

    def animate(self, fTime):
        global viewTime
        if viewTime >= fTime:
            return
        #print(viewTime)
        viewTime += timedelta(days = 1)
        self.updateGL()
        QTimer.singleShot(50, (lambda: self.animate(fTime)))

    def resizeGL(self, w, h):
        vis.reshape(w, h)

    def initializeGL(self):
        global ephem

        if not self.initted:
            vis.init(1024, 720)
            for i in vis.planets:
                vis.planets[i].body = ephem.get_body(i)
        self.initted = True

    def mClick(self, button, state, x, y):
        vis.mouseclick(button, state, x, y)
        self.updateGL()

    def mDrag(self, x, y):
        vis.mousemotion(x, y)
        self.updateGL()

    def kPress(self, key):
        vis.keydown(key, 0, 0)
        self.updateGL()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    #loading screen
    loading = QSplashScreen(QPixmap('assets/loading-min.jpg').scaled(640,480))
    loading.show()
    loading.setStyleSheet('font-size: 18pt; font-family: Courier; color: rgb(255, 255, 255)')
    loading.showMessage("picture by NASA/JPL-Caltech/Univ. of Arizona\nMars Reconnaissance Orbiter (MRO)\nid: PIA17646")

    #SPICE initializations
    global ephem
    root_dir = os.path.abspath(os.getcwd())
    ephem = ephemeris(sp, root_dir)

    global solarSystemPlaneUP
    e2001 = ephem.get_body('EARTH').state(datetime(2001,1,1))
    e2001UP = np.cross(np.array(e2001[0:3]), np.array(e2001[3:]))
    solarSystemPlaneUP = e2001UP / np.linalg.norm(e2001UP)

    #initialize main window
    global window
    window = MainWindow()

    window.show()
    #splash.close()
    loading.finish(window)

    app.exec_()
