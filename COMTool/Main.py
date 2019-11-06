import sys, os

try:
    import parameters, helpAbout, autoUpdate
    from Combobox import ComboBox
except ImportError:
    from COMTool import parameters, helpAbout, autoUpdate
    from COMTool.Combobox import ComboBox

# from COMTool.wave import Wave
from PyQt5.QtCore import pyqtSignal, Qt, QMargins
from PyQt5.QtWidgets import (QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QDesktopWidget, QMainWindow,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QTextEdit, QLabel, QRadioButton, QCheckBox,
                             QLineEdit, QGroupBox, QSplitter, QFileDialog)
from PyQt5.QtGui import QIcon, QFont, QTextCursor, QPixmap, QBrush, QColor
from PyQt5.QtChart import *
from PyQt5.QtChart import QChartView
import serial
import serial.tools.list_ports
import threading
import time
import binascii, re

try:
    import cPickle as pickle
except ImportError:
    import pickle
if sys.platform == "win32":
    import ctypes


class MyClass(object):
    def __init__(self, arg):
        super(MyClass, self).__init__()
        self.arg = arg


class MainWindow(QMainWindow):
    beginCheckUVWZTime=0
    foundZ=False
    receiveUpdateSignal = pyqtSignal(str)
    setSendTextSignal=pyqtSignal(str)
    updateChartSignal = pyqtSignal()
    errorSignal = pyqtSignal(str)
    showSerialComboboxSignal = pyqtSignal()
    setDisableSettingsSignal = pyqtSignal(bool)
    isDetectSerialPort = False
    receiveCount = 0
    sendCount = 0
    isScheduledSending = False
    DataPath = "./"
    isHideSettings = False
    isHideFunctinal = True
    app = None
    isWaveOpen = False
    receiveBytes = bytearray()
    cmdSendQuen = []
    cmdGotRsp = True
    I=0

    def __init__(self, app):
        super().__init__()
        self.app = app
        pathDirList = sys.argv[0].replace("\\", "/").split("/")
        pathDirList.pop()
        self.DataPath = os.path.abspath("/".join(str(i) for i in pathDirList))
        if not os.path.exists(self.DataPath + "/" + parameters.strDataDirName):
            pathDirList.pop()
            self.DataPath = os.path.abspath("/".join(str(i) for i in pathDirList))
        self.DataPath = (self.DataPath + "/" + parameters.strDataDirName).replace("\\", "/")
        self.initWindow()
        self.initTool()
        self.initEvent()
        self.programStartGetSavedParameters()

    def __del__(self):
        pass

    def initTool(self):
        self.com = serial.Serial()

    def initWindow(self):
        QToolTip.setFont(QFont('SansSerif', 10))
        # main layout
        frameWidget = QWidget()
        mainWidget = QSplitter(Qt.Horizontal)
        frameLayout = QVBoxLayout()
        self.settingWidget = QWidget()
        self.settingWidget.setProperty("class", "settingWidget")
        self.receiveSendWidget = QSplitter(Qt.Vertical)
        self.functionalWiget = QWidget()
        self.functionalWiget.setMaximumWidth(280)
        settingLayout = QVBoxLayout()
        sendReceiveLayout = QVBoxLayout()
        infoW = QGroupBox("info")
        sendFunctionalLayout = QVBoxLayout()
        mainLayout = QHBoxLayout()
        self.settingWidget.setLayout(settingLayout)
        self.receiveSendWidget.setLayout(sendReceiveLayout)
        self.functionalWiget.setLayout(sendFunctionalLayout)
        mainLayout.addWidget(self.settingWidget)
        mainLayout.addWidget(self.receiveSendWidget)
        mainLayout.addWidget(self.functionalWiget)
        mainLayout.setStretch(0, 3)
        mainLayout.setStretch(1, 10)
        mainLayout.setStretch(2, 4)
        menuLayout = QHBoxLayout()
        mainWidget.setLayout(mainLayout)
        frameLayout.addLayout(menuLayout)
        frameLayout.addWidget(mainWidget)
        frameWidget.setLayout(frameLayout)
        self.setCentralWidget(frameWidget)

        # option layout
        self.settingsButton = QPushButton()
        self.skinButton = QPushButton("")
        # self.waveButton = QPushButton("")
        self.aboutButton = QPushButton()
        self.functionalButton = QPushButton()
        self.encodingCombobox = ComboBox()
        self.encodingCombobox.addItem("ASCII")
        self.encodingCombobox.addItem("UTF-8")
        self.encodingCombobox.addItem("UTF-16")
        self.encodingCombobox.addItem("GBK")
        self.encodingCombobox.addItem("GB2312")
        self.encodingCombobox.addItem("GB18030")
        self.settingsButton.setProperty("class", "menuItem1")
        self.skinButton.setProperty("class", "menuItem2")
        self.aboutButton.setProperty("class", "menuItem3")
        self.functionalButton.setProperty("class", "menuItem4")
        # self.waveButton.setProperty("class", "menuItem5")
        self.settingsButton.setObjectName("menuItem")
        self.skinButton.setObjectName("menuItem")
        self.aboutButton.setObjectName("menuItem")
        self.functionalButton.setObjectName("menuItem")
        # self.waveButton.setObjectName("menuItem")
        menuLayout.addWidget(self.settingsButton)
        menuLayout.addWidget(self.skinButton)
        # menuLayout.addWidget(self.waveButton)
        menuLayout.addWidget(self.aboutButton)
        self.aboutButton.hide()
        self.debug = QPushButton("debug")
        self.clearErr=QPushButton("清除错误")
        # debug.setProperty("class","menuItem")
        menuLayout.addWidget(self.debug)
        menuLayout.addWidget(self.clearErr)
        menuLayout.addStretch(0)
        menuLayout.addWidget(self.encodingCombobox)
        self.encodingCombobox.hide()
        menuLayout.addWidget(self.functionalButton)

        # widgets receive and send area
        self.receiveArea = QTextEdit()
        self.sendArea = QTextEdit()
        self.sendArea.setMinimumHeight(30)
        self.sendArea.setMaximumHeight(80)
        self.receiveArea.setMinimumHeight(30)
        self.receiveArea.setMaximumHeight(80)
        self.clearReceiveButtion = QPushButton(parameters.strClearReceive)
        self.sendButtion = QPushButton(parameters.strSend)
        self.sendHistory = ComboBox()
        sendWidget = QWidget()
        sendAreaWidgetsLayout = QHBoxLayout()
        sendWidget.setLayout(sendAreaWidgetsLayout)
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.clearReceiveButtion)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.sendButtion)
        sendAreaWidgetsLayout.addWidget(self.sendArea)
        sendAreaWidgetsLayout.addLayout(buttonLayout)

        self.receiveArea.hide()
        self.sendArea.hide()
        self.sendButtion.hide()
        self.clearReceiveButtion.hide()

        self.speedChart = QChart()
        self.speedChart.setBackgroundBrush(QBrush(QColor(0x21, 0x21, 0x21)))
        self.speedChart.legend().hide()

        # speedChart.setPlotAreaBackgroundBrush(QBrush(QColor(0x21,0x21,0x21)))
        # speedChart.setPlotAreaBackgroundVisible(True)

        self.speedChartView = QChartView(self.speedChart)
        self.speedChart.setMargins(QMargins(0, 0, 0, 0))

        self.seriesRealSpeed = QLineSeries()
        self.seriesRealSpeed.setName("real")
        self.seriesRealSpeed.append(0, 0)
        self.seriesRealSpeed.append(1, 3)
        self.seriesRealSpeed.append(2, 13)

        self.seriesTargetSpeed = QLineSeries()
        self.seriesTargetSpeed.setName("real")
        self.seriesTargetSpeed.append(0, 0)
        self.seriesTargetSpeed.append(1, 15)
        self.seriesTargetSpeed.append(2, 15)

        self.seriesPower = QLineSeries()
        self.seriesPower.append(0, 0)
        self.seriesPower.append(1, 15)
        self.seriesPower.append(2, 25)

        self.I=2;

        self.speedChart.addSeries(self.seriesRealSpeed)
        self.speedChart.addSeries(self.seriesTargetSpeed)
        self.speedChart.addSeries(self.seriesPower)

        self.speedChart.createDefaultAxes()
        self.speedChart.axisX().setGridLineVisible(False)
        self.speedChart.axisY().setGridLineVisible(False)
        # speedChart.setTitle("速度及电压")

        # self.speedChart.show()
        sendReceiveLayout.addWidget(infoW)
        sendReceiveLayout.addWidget(self.speedChartView)

        sendReceiveLayout.addWidget(self.receiveArea)
        sendReceiveLayout.addWidget(sendWidget)
        sendReceiveLayout.addWidget(self.sendHistory)
        self.sendHistory.hide()
        sendReceiveLayout.setStretch(0, 1)
        sendReceiveLayout.setStretch(1, 7)
        sendReceiveLayout.setStretch(2, 1)
        sendReceiveLayout.setStretch(3, 1)

        # widgets serial settings
        serialSettingsGroupBox = QGroupBox(parameters.strSerialSettings)
        serialSettingsGroupBoxAdvance = QGroupBox("advance port setting")
        serialSettingsLayout = QGridLayout()
        serialSettingsLayoutAdvance = QGridLayout()
        serialReceiveSettingsLayout = QGridLayout()
        serialSendSettingsLayout = QGridLayout()
        serialPortLabek = QLabel(parameters.strSerialPort)
        serailBaudrateLabel = QLabel(parameters.strSerialBaudrate)
        serailBytesLabel = QLabel(parameters.strSerialBytes)
        serailParityLabel = QLabel(parameters.strSerialParity)
        serailStopbitsLabel = QLabel(parameters.strSerialStopbits)
        self.serialPortCombobox = ComboBox()
        self.serailBaudrateCombobox = ComboBox()
        self.serailBaudrateCombobox.addItem("9600")
        self.serailBaudrateCombobox.addItem("19200")
        self.serailBaudrateCombobox.addItem("38400")
        self.serailBaudrateCombobox.addItem("57600")
        self.serailBaudrateCombobox.addItem("115200")
        self.serailBaudrateCombobox.setCurrentIndex(0)
        self.serailBaudrateCombobox.setEditable(True)
        self.serailBytesCombobox = ComboBox()
        self.serailBytesCombobox.addItem("5")
        self.serailBytesCombobox.addItem("6")
        self.serailBytesCombobox.addItem("7")
        self.serailBytesCombobox.addItem("8")
        self.serailBytesCombobox.setCurrentIndex(3)
        self.serailParityCombobox = ComboBox()
        self.serailParityCombobox.addItem("None")
        self.serailParityCombobox.addItem("Odd")
        self.serailParityCombobox.addItem("Even")
        self.serailParityCombobox.addItem("Mark")
        self.serailParityCombobox.addItem("Space")
        self.serailParityCombobox.setCurrentIndex(0)
        self.serailStopbitsCombobox = ComboBox()
        self.serailStopbitsCombobox.addItem("1")
        self.serailStopbitsCombobox.addItem("1.5")
        self.serailStopbitsCombobox.addItem("2")
        self.serailStopbitsCombobox.setCurrentIndex(0)
        self.checkBoxRts = QCheckBox("rts")
        self.checkBoxDtr = QCheckBox("dtr")
        self.serialOpenCloseButton = QPushButton(parameters.strOpen)
        # serialSettingsLayout.addWidget(serialPortLabek, 0, 0)
        serialSettingsLayoutAdvance.addWidget(serailBaudrateLabel, 1, 0)
        serialSettingsLayoutAdvance.addWidget(serailBytesLabel, 2, 0)
        serialSettingsLayoutAdvance.addWidget(serailParityLabel, 3, 0)
        serialSettingsLayoutAdvance.addWidget(serailStopbitsLabel, 4, 0)
        serialSettingsLayout.addWidget(self.serialPortCombobox, 0, 0, 1, 2)
        serialSettingsLayoutAdvance.addWidget(self.serailBaudrateCombobox, 1, 1)
        serialSettingsLayoutAdvance.addWidget(self.serailBytesCombobox, 2, 1)
        serialSettingsLayoutAdvance.addWidget(self.serailParityCombobox, 3, 1)
        serialSettingsLayoutAdvance.addWidget(self.serailStopbitsCombobox, 4, 1)
        serialSettingsLayoutAdvance.addWidget(self.checkBoxRts, 5, 0, 1, 1)
        serialSettingsLayoutAdvance.addWidget(self.checkBoxDtr, 5, 1, 1, 1)
        serialSettingsLayout.addWidget(self.serialOpenCloseButton, 6, 0, 1, 2)
        serialSettingsGroupBox.setLayout(serialSettingsLayout)
        # settingLayout.addWidget(serialSettingsGroupBox)

        serialSettingsGroupBoxAdvance.setLayout(serialSettingsLayoutAdvance)
        settingLayout.addWidget(serialSettingsGroupBoxAdvance)
        serialSettingsGroupBoxAdvance.hide()

        # serial receive settings
        serialReceiveSettingsGroupBox = QGroupBox(parameters.strSerialReceiveSettings)
        self.receiveSettingsAscii = QRadioButton(parameters.strAscii)
        self.receiveSettingsHex = QRadioButton(parameters.strHex)
        self.receiveSettingsAscii.setChecked(True)
        self.receiveSettingsAutoLinefeed = QCheckBox(parameters.strAutoLinefeed)
        self.receiveSettingsAutoLinefeedTime = QLineEdit(parameters.strAutoLinefeedTime)
        self.receiveSettingsAutoLinefeed.setMaximumWidth(75)
        self.receiveSettingsAutoLinefeedTime.setMaximumWidth(75)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsAscii, 1, 0, 1, 1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsHex, 1, 1, 1, 1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsAutoLinefeed, 2, 0, 1, 1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsAutoLinefeedTime, 2, 1, 1, 1)
        serialReceiveSettingsGroupBox.setLayout(serialReceiveSettingsLayout)
        settingLayout.addWidget(serialReceiveSettingsGroupBox)
        serialReceiveSettingsGroupBox.hide()

        # serial send settings
        serialSendSettingsGroupBox = QGroupBox(parameters.strSerialSendSettings)
        self.sendSettingsAscii = QRadioButton(parameters.strAscii)
        self.sendSettingsHex = QRadioButton(parameters.strHex)
        self.sendSettingsAscii.setChecked(True)
        self.sendSettingsScheduledCheckBox = QCheckBox(parameters.strScheduled)
        self.sendSettingsScheduled = QLineEdit(parameters.strScheduledTime)
        self.sendSettingsScheduledCheckBox.setMaximumWidth(75)
        self.sendSettingsScheduled.setMaximumWidth(75)
        self.sendSettingsCFLF = QCheckBox(parameters.strCRLF)
        self.sendSettingsCFLF.setChecked(False)
        serialSendSettingsLayout.addWidget(self.sendSettingsAscii, 1, 0, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsHex, 1, 1, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsScheduledCheckBox, 2, 0, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsScheduled, 2, 1, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsCFLF, 3, 0, 1, 2)
        serialSendSettingsGroupBox.setLayout(serialSendSettingsLayout)
        settingLayout.addWidget(serialSendSettingsGroupBox)
        serialSendSettingsGroupBox.hide()

        # settingLayout.setStretch(0, 5)
        # settingLayout.setStretch(1, 2.5)
        # settingLayout.setStretch(2, 2.5)

        settingLayout.addStretch(1)

        # right functional layout

        # self begin
        self.checkWidget = QGroupBox("基本检查");
        checkWidgetLayout = QVBoxLayout();
        self.checkWidget.setLayout(checkWidgetLayout)
        self.checkButton=QPushButton("check uvwz")
        checkWidgetLayout.addWidget(self.checkButton)

        setPowerLayout = QHBoxLayout()

        self.maxPowerEdit=QLineEdit("25");
        setPowerLayout.addWidget(self.maxPowerEdit)
        self.setMaxPowerButton=QPushButton("设置最大电压")
        setPowerLayout.addWidget(self.setMaxPowerButton)
        setPowerLayout.setStretch(1, 1)
        setPowerLayout.setStretch(2, 1)
        checkWidgetLayout.addLayout(setPowerLayout)

        infoWLayout = QVBoxLayout()
        infoW.setLayout(infoWLayout)
        infoW.setDisabled(True)

        self.signalU = QCheckBox("U  ")
        self.signalV = QCheckBox("V  ")
        self.signalW = QCheckBox("W  ")
        self.signalZ = QCheckBox("Z  ")

        signalLayout = QHBoxLayout()
        signalLayout.addWidget(self.signalU)
        signalLayout.addWidget(self.signalV)
        signalLayout.addWidget(self.signalW)
        signalLayout.addWidget(self.signalZ)
        signalLayout.addSpacing(30)
        signalLayout.addWidget(QLabel("机械角度："))
        self.angle = QLabel("0")
        signalLayout.addWidget(self.angle)
        signalLayout.addStretch(1)

        self.errorLabel = QLabel("未连接")
        errorLayout = QHBoxLayout()
        errorLayout.addWidget(QLabel("当前状态："))
        errorLayout.addWidget(self.errorLabel)
        errorLayout.addStretch(1)
        infoWLayout.addLayout(errorLayout)
        infoWLayout.addLayout(signalLayout)

        sendFunctionalLayout.addWidget(serialSettingsGroupBox)
        sendFunctionalLayout.addWidget(self.checkWidget)

        self.runWidget = QGroupBox("运行测试")
        runWidgetLayout = QVBoxLayout()
        self.runWidget.setLayout(runWidgetLayout)

        slowLayout = QHBoxLayout()
        midLayout = QHBoxLayout()
        fastLayout = QHBoxLayout()

        self.lowSpeed=QLineEdit("200")
        slowLayout.addWidget(self.lowSpeed)
        self.lowRunButton=QPushButton("运行")
        slowLayout.addWidget(self.lowRunButton)


        runWidgetLayout.addLayout(slowLayout)
        self.midSpeed=QLineEdit("1000")
        midLayout.addWidget(self.midSpeed)
        self.midRunButton=QPushButton("运行")
        midLayout.addWidget(self.midRunButton)
        runWidgetLayout.addLayout(midLayout)

        self.highSpeed=QLineEdit("2000")
        fastLayout.addWidget(self.highSpeed)
        self.highRunButton=QPushButton("运行")
        fastLayout.addWidget(self.highRunButton)
        runWidgetLayout.addLayout(fastLayout)

        sendFunctionalLayout.addWidget(self.runWidget)
        self.runWidget.setDisabled(True)
        self.checkWidget.setDisabled(True)

        # self end

        self.filePathWidget = QLineEdit()
        self.openFileButton = QPushButton("Open File")
        self.sendFileButton = QPushButton("Send File")
        self.clearHistoryButton = QPushButton("Clear History")
        self.addButton = QPushButton("停止")

        fileSendGroupBox = QGroupBox(parameters.strSendFile)
        fileSendGridLayout = QGridLayout()
        fileSendGridLayout.addWidget(self.filePathWidget, 0, 0, 1, 1)
        fileSendGridLayout.addWidget(self.openFileButton, 0, 1, 1, 1)
        fileSendGridLayout.addWidget(self.sendFileButton, 1, 0, 1, 2)
        fileSendGroupBox.setLayout(fileSendGridLayout)
        sendFunctionalLayout.addWidget(fileSendGroupBox)
        fileSendGroupBox.hide()
        sendFunctionalLayout.addWidget(self.clearHistoryButton)
        self.clearHistoryButton.hide()
        sendFunctionalLayout.addWidget(self.addButton)
        sendFunctionalLayout.addStretch(1)
        self.isHideFunctinal = False
        self.showFunctional()
        self.isHideSettings = True
        self.hideSettings()

        # main window
        self.statusBarStauts = QLabel()
        self.statusBarStauts.setMinimumWidth(80)
        self.statusBarStauts.setText("<font color=%s>%s</font>" % ("#008200", parameters.strReady))
        self.statusBarSendCount = QLabel(parameters.strSend + "(bytes): " + "0")
        self.statusBarReceiveCount = QLabel(parameters.strReceive + "(bytes): " + "0")
        self.statusBar().addWidget(self.statusBarStauts)
        self.statusBar().addWidget(self.statusBarSendCount, 2)
        self.statusBar().addWidget(self.statusBarReceiveCount, 3)
        # self.statusBar()

        self.resize(800, 500)
        self.MoveToCenter()
        self.setWindowTitle(parameters.appName + " V" + str(helpAbout.versionMajor) + "." + str(helpAbout.versionMinor))
        icon = QIcon()
        print("icon path:" + self.DataPath + "/" + parameters.appIcon)
        icon.addPixmap(QPixmap(self.DataPath + "/" + parameters.appIcon), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)
        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("comtool")
        self.show()
        print("config file path:", parameters.configFilePath)

    def setMaxPower(self):
        maxPower=int(self.maxPowerEdit.text());
        self.cmdSendQuen.append(bytes([0x90, 92, 0x00,maxPower , 0x90 ^ 92 ^ 0x00 ^ maxPower]))

    def checkuvwz(self):
        self.findZ=False
        self.beginCheckUVWZTime=time.time()
        self.cmdSendQuen.append(bytes([0x90, 0x65,0x00,0x07,0x90^0x65^0x00^0x07]))

    def stopMotor(self):
        self.cmdSendQuen.append(bytes([0x90, 0x65, 0x00, 0x00, 0x90 ^ 0x65 ^ 0x00 ^ 0x00]))



    def updateChart(self):
        self.speedChart.removeSeries(self.seriesTargetSpeed)
        self.speedChart.removeSeries(self.seriesRealSpeed)
        self.speedChart.removeSeries(self.seriesPower)
        self.speedChart.addSeries(self.seriesTargetSpeed)
        self.speedChart.addSeries(self.seriesRealSpeed)
        self.speedChart.addSeries(self.seriesPower)

        self.speedChart.createDefaultAxes()
        self.speedChart.axisX().setGridLineVisible(False)
        self.speedChart.axisY().setGridLineVisible(False)

    def runAsSpeed(self, speed):
        interSpeed = int(speed/43.0)
        self.cmdSendQuen.append(bytes([0x90, 101, 0, interSpeed, 0x90 ^ 101 ^ interSpeed]))

    def lowRun(self):
        self.runAsSpeed(int(self.lowSpeed.text()))
    def midRun(self):
        self.runAsSpeed(int(self.midSpeed.text()))
    def highRun(self):
        self.runAsSpeed(int(self.highSpeed.text()))

    def clearMoterErr(self):
        self.cmdSendQuen.append(bytes([0x90,101,0,0xFF,0x90^101^0xFF]))

    def initEvent(self):
        self.clearErr.clicked.connect(self.clearMoterErr)

        self.lowRunButton.clicked.connect(self.lowRun)
        self.midRunButton.clicked.connect(self.midRun)
        self.highRunButton.clicked.connect(self.highRun)

        self.setMaxPowerButton.clicked.connect(self.setMaxPower)
        self.checkButton.clicked.connect(self.checkuvwz)
        self.serialOpenCloseButton.clicked.connect(self.openCloseSerial)
        self.sendButtion.clicked.connect(self.sendData)
        self.receiveUpdateSignal.connect(self.updateReceivedDataDisplay)
        self.setSendTextSignal.connect(self.setSendText)
        self.updateChartSignal.connect(self.updateChart)
        self.clearReceiveButtion.clicked.connect(self.clearReceiveBuffer)
        self.serialPortCombobox.clicked.connect(self.portComboboxClicked)
        self.sendSettingsHex.clicked.connect(self.onSendSettingsHexClicked)
        self.sendSettingsAscii.clicked.connect(self.onSendSettingsAsciiClicked)
        self.errorSignal.connect(self.errorHint)
        self.showSerialComboboxSignal.connect(self.showCombobox)
        # self.showBaudComboboxSignal.connect(self.showBaudCombobox)
        self.setDisableSettingsSignal.connect(self.setDisableSettings)
        self.sendHistory.currentIndexChanged.connect(self.sendHistoryIndexChanged)
        self.settingsButton.clicked.connect(self.showHideSettings)
        self.skinButton.clicked.connect(self.skinChange)
        self.debug.clicked.connect(self.debugClick)
        self.aboutButton.clicked.connect(self.showAbout)
        self.openFileButton.clicked.connect(self.selectFile)
        self.sendFileButton.clicked.connect(self.sendFile)
        self.clearHistoryButton.clicked.connect(self.clearHistory)
        self.addButton.clicked.connect(self.stopMotor)
        self.functionalButton.clicked.connect(self.showHideFunctional)
        self.sendArea.currentCharFormatChanged.connect(self.sendAreaFontChanged)
        # self.waveButton.clicked.connect(self.openWaveDisplay)
        self.checkBoxRts.clicked.connect(self.rtsChanged)
        self.checkBoxDtr.clicked.connect(self.dtrChanged)

        self.myObject = MyClass(self)
        slotLambda = lambda: self.indexChanged_lambda(self.myObject)
        self.serialPortCombobox.currentIndexChanged.connect(slotLambda)

    # @QtCore.pyqtSlot(str)
    def indexChanged_lambda(self, obj):
        mainObj = obj.arg
        # print("item changed:",mainObj.serialPortCombobox.currentText())
        self.serialPortCombobox.setToolTip(mainObj.serialPortCombobox.currentText())

    def openCloseSerialProcess(self):
        try:
            if self.com.is_open:
                self.receiveProgressStop = True
                self.com.close()
                self.setDisableSettingsSignal.emit(False)
                self.errorLabel.setText("连接断开")
            else:
                try:
                    self.com.baudrate = int(self.serailBaudrateCombobox.currentText())
                    self.com.port = self.serialPortCombobox.currentText().split(" ")[0]
                    self.com.bytesize = int(self.serailBytesCombobox.currentText())
                    self.com.parity = self.serailParityCombobox.currentText()[0]
                    self.com.stopbits = float(self.serailStopbitsCombobox.currentText())
                    self.com.timeout = None
                    if self.checkBoxRts.isChecked():
                        self.com.rts = False
                    else:
                        self.com.rts = True
                    if self.checkBoxDtr.isChecked():
                        self.com.dtr = False
                    else:
                        self.com.dtr = True
                    self.com.open()
                    # print("open success")
                    # print(self.com)
                    self.receiveProgressStop = False
                    self.setDisableSettingsSignal.emit(True)
                    self.receiveProcess = threading.Thread(target=self.receiveData)
                    self.receiveProcess.setDaemon(True)
                    self.receiveProcess.start()

                    self.cmdGotRsp = True
                    self.cmdSendQuen.clear()
                    self.sendQuenProcess = threading.Thread(target=self.sendQuen)
                    self.sendQuenProcess.setDaemon(True)
                    self.sendQuenProcess.start()

                    self.errorLabel.setText("连接成功")

                    self.readStatusCmdGenThread = threading.Thread(target=self.readStatusCmdGen)
                    self.readStatusCmdGenThread.setDaemon(True)
                    self.readStatusCmdGenThread.start()

                except Exception as e:
                    self.com.close()
                    self.receiveProgressStop = True
                    self.errorSignal.emit(parameters.strOpenFailed + "\n" + str(e))
                    self.setDisableSettingsSignal.emit(False)
        except Exception as e:
            print(e)

    def setDisableSettings(self, disable):
        if disable:
            self.serialOpenCloseButton.setText(parameters.strClose)
            self.statusBarStauts.setText("<font color=%s>%s</font>" % ("#008200", parameters.strReady))
            self.serialPortCombobox.setDisabled(True)
            self.serailBaudrateCombobox.setDisabled(True)
            self.serailParityCombobox.setDisabled(True)
            self.serailStopbitsCombobox.setDisabled(True)
            self.serailBytesCombobox.setDisabled(True)
            self.serialOpenCloseButton.setDisabled(False)
        else:
            self.serialOpenCloseButton.setText(parameters.strOpen)
            self.statusBarStauts.setText("<font color=%s>%s</font>" % ("#f31414", parameters.strClosed))
            self.serialPortCombobox.setDisabled(False)
            self.serailBaudrateCombobox.setDisabled(False)
            self.serailParityCombobox.setDisabled(False)
            self.serailStopbitsCombobox.setDisabled(False)
            self.serailBytesCombobox.setDisabled(False)
            self.programExitSaveParameters()

    def openCloseSerial(self):
        t = threading.Thread(target=self.openCloseSerialProcess)
        t.setDaemon(True)
        t.start()

    def rtsChanged(self):
        if self.checkBoxRts.isChecked():
            self.com.setRTS(False)
        else:
            self.com.setRTS(True)

    def dtrChanged(self):
        if self.checkBoxDtr.isChecked():
            self.com.setDTR(False)
        else:
            self.com.setDTR(True)

    def portComboboxClicked(self):
        self.detectSerialPort()

    def getSendData(self):
        data = self.sendArea.toPlainText()
        if self.sendSettingsCFLF.isChecked():
            data = data.replace("\n", "\r\n")
        if self.sendSettingsHex.isChecked():
            if self.sendSettingsCFLF.isChecked():
                data = data.replace("\r\n", " ")
            else:
                data = data.replace("\n", " ")
            data = self.hexStringB2Hex(data)
            if data == -1:
                self.errorSignal.emit(parameters.strWriteFormatError)
                return -1
        else:
            data = data.encode(self.encodingCombobox.currentText(), "ignore")
        return data

    def sendData(self):
        try:
            if self.com.is_open:
                data = self.getSendData()
                if data == -1:
                    return
                # print(self.sendArea.toPlainText())
                # print("send:",data)
                self.sendCount += len(data)
                for c in data:
                    self.com.write(bytes([c]))
                    time.sleep(0.01)

                data = self.sendArea.toPlainText()
                self.sendHistoryFindDelete(data)
                self.sendHistory.insertItem(0, data)
                self.sendHistory.setCurrentIndex(0)
                self.receiveUpdateSignal.emit("")
                # scheduled send
                if self.sendSettingsScheduledCheckBox.isChecked():
                    if not self.isScheduledSending:
                        t = threading.Thread(target=self.scheduledSend)
                        t.setDaemon(True)
                        t.start()
        except Exception as e:
            self.errorLabel.setText("发送出错" + str(e))
            # self.errorSignal.emit(parameters.strWriteError)
            # print(e)

    def scheduledSend(self):
        self.isScheduledSending = True
        while self.sendSettingsScheduledCheckBox.isChecked():
            self.sendData()
            try:
                time.sleep(int(self.sendSettingsScheduled.text().strip()) / 1000)
            except Exception:
                self.errorSignal.emit(parameters.strTimeFormatError)
        self.isScheduledSending = False



    def readStatusCmdGen(self):
        while (not self.receiveProgressStop):
            if self.beginCheckUVWZTime > 0 and time.time() - self.beginCheckUVWZTime > 2:
                if self.foundZ:
                    self.errorLabel.setText("check pass")
                else:
                    self.errorLabel.setText("found z failed")
                self.runWidget.setDisabled(not self.foundZ)
                self.stopMotor()
                self.beginCheckUVWZTime=0
            while self.cmdSendQuen:
                time.sleep(1)
                continue
            self.I+=1;
            self.cmdSendQuen.append(bytes([0x68, 101, 0x68 ^ 101]))
            self.cmdSendQuen.append(bytes([0x68, 102, 0x68 ^ 102]))
            #self.cmdSendQuen.append(bytes([0x68, 92, 0x68 ^ 92]))
            self.cmdSendQuen.append(bytes([0x68, 103, 0x68 ^ 103]))
            self.cmdSendQuen.append(bytes([0x68, 104, 0x68 ^ 104]))
            self.cmdSendQuen.append(bytes([0x68, 105, 0x68 ^ 105]))


    def sendQuen(self):
        self.timeLastSend = 0
        while (not self.receiveProgressStop):
            if not self.cmdGotRsp:
                if time.time() - self.timeLastSend > 1:
                    self.errorLabel.setText("响应超时")
                time.sleep(0.1)
                continue
            if not self.cmdSendQuen:
                time.sleep(0.1)
                continue
            cmd = self.cmdSendQuen[0]
            cmdstr = self.asciiB2HexString(cmd)
            self.setSendTextSignal.emit(cmdstr)
            while not self.sendArea.toPlainText() == cmdstr:
                time.sleep(0.001)
            self.cmdGotRsp = False
            self.sendData()
            self.timeLastSend = time.time()

            del self.cmdSendQuen[0]

    def receiveData(self):
        self.timeLastReceive = 0
        while (not self.receiveProgressStop):
            try:
                # length = self.com.in_waiting
                length = max(1, min(2048, self.com.in_waiting))
                bytesR = self.com.read(length)
                if bytesR is not None:

                    self.receiveBytes += bytesR
                    # if self.isWaveOpen:
                    #     self.wave.displayData(bytes)
                    self.receiveCount += len(bytesR)

                    if self.receiveSettingsAutoLinefeed.isChecked():
                        if time.time() - self.timeLastReceive > int(self.receiveSettingsAutoLinefeedTime.text()) / 1000:
                            if self.sendSettingsCFLF.isChecked():
                                self.receiveUpdateSignal.emit("\r\n")
                            else:
                                self.receiveUpdateSignal.emit("\n")
                            self.timeLastReceive = time.time()
                    if self.receiveSettingsHex.isChecked():

                        # popup wrong data
                        for i in range(0, len(self.receiveBytes)):
                            if self.receiveBytes[0] & 0xf8 is not 0x90 and self.receiveBytes[0] & 0xf8 is not 0x68:
                                self.receiveUpdateSignal.emit(self.asciiB2HexString(self.receiveBytes[0:1]))
                                del self.receiveBytes[0]

                        if len(self.receiveBytes) >= 5:
                            # todo check crc
                            if self.receiveBytes[0] & 0xF8 == 0x68:
                                # read cmd
                                self.receiveUpdateSignal.emit(self.asciiB2HexString(self.receiveBytes[0:5]))
                                if self.receiveBytes[1] == 101:
                                    self.signalU.setChecked(self.receiveBytes[3] & 0x1)
                                    self.signalV.setChecked(self.receiveBytes[3] & 0x2)
                                    self.signalW.setChecked(self.receiveBytes[3] & 0x4)
                                    self.signalZ.setChecked(self.receiveBytes[3] & 0x8)
                                elif self.receiveBytes[1] == 102:
                                    if self.receiveBytes[3] :
                                        self.errorLabel.setText("故障代码"+str(self.receiveBytes[3]))
                                    else :
                                        self.checkWidget.setDisabled(False)
                                elif self.receiveBytes[1] == 92 :
                                    self.maxPowerEdit.setText(str(self.receiveBytes[3]))
                                elif self.receiveBytes[1] == 105:
                                    angle=self.receiveBytes[2]*(1<<8)+self.receiveBytes[3]
                                    if not angle == 0 :
                                        self.foundZ=True
                                    self.angle.setText(str(angle))
                                elif self.receiveBytes[1] == 103:
                                    # es and power
                                    self.seriesPower.append(self.I,self.receiveBytes[3])
                                    if self.seriesPower.count() > 50:
                                        self.seriesPower.remove(0)
                                elif self.receiveBytes[1] == 104:
                                    # real and target in rpm/100
                                    self.seriesRealSpeed.append(self.I, self.receiveBytes[2])
                                    self.seriesTargetSpeed.append(self.I,self.receiveBytes[3])
                                    if self.seriesTargetSpeed.count() > 50:
                                        self.seriesTargetSpeed.remove(0)
                                    if self.seriesRealSpeed.count() > 50:
                                        self.seriesRealSpeed.remove(0)

                                    self.updateChartSignal.emit()


                                del self.receiveBytes[0:5]
                            elif self.receiveBytes[0] & 0xf8 == 0x90:
                                # write cmd
                                self.receiveUpdateSignal.emit(self.asciiB2HexString(self.receiveBytes[0:5]))

                                if self.receiveBytes[1] == 92 :
                                    self.maxPowerEdit.setText(str(self.receiveBytes[3]))

                                del self.receiveBytes[0:5]
                            self.receiveUpdateSignal.emit("\n")
                            self.cmdGotRsp = True
                    else:
                        self.receiveUpdateSignal.emit(bytesR.decode(self.encodingCombobox.currentText(), "ignore"))
            except Exception as e:
                # print("receiveData error")
                # if self.com.is_open and not self.serialPortCombobox.isEnabled():
                #     self.openCloseSerial()
                #     self.serialPortCombobox.clear()
                #     self.detectSerialPort()
                if 'multiple access' in str(e):
                    self.errorSignal.emit("device disconnected or multiple access on port?")
                break
            # time.sleep(0.009)

    def updateReceivedDataDisplay(self, str):
        if str != "":
            curScrollValue = self.receiveArea.verticalScrollBar().value()
            self.receiveArea.moveCursor(QTextCursor.End)
            endScrollValue = self.receiveArea.verticalScrollBar().value()
            self.receiveArea.insertPlainText(str)
            if curScrollValue < endScrollValue:
                self.receiveArea.verticalScrollBar().setValue(curScrollValue)
            else:
                self.receiveArea.moveCursor(QTextCursor.End)
        self.statusBarSendCount.setText("%s(bytes):%d" % (parameters.strSend, self.sendCount))
        self.statusBarReceiveCount.setText("%s(bytes):%d" % (parameters.strReceive, self.receiveCount))

    def setSendText(self,str):
        self.sendArea.setText(str)


    def onSendSettingsHexClicked(self):

        data = self.sendArea.toPlainText().replace("\n", "\r\n")
        data = self.asciiB2HexString(data.encode())
        self.sendArea.clear()
        self.sendArea.insertPlainText(data)

    def onSendSettingsAsciiClicked(self):
        try:
            data = self.sendArea.toPlainText().replace("\n", " ").strip()
            self.sendArea.clear()
            if data != "":
                data = self.hexStringB2Hex(data).decode(self.encodingCombobox.currentText(), 'ignore')
                self.sendArea.insertPlainText(data)
        except Exception as e:
            # QMessageBox.information(self,parameters.strWriteFormatError,parameters.strWriteFormatError)
            print("format error")

    def sendHistoryIndexChanged(self):
        self.sendArea.clear()
        self.sendArea.insertPlainText(self.sendHistory.currentText())

    def clearReceiveBuffer(self):
        self.receiveArea.clear()
        self.receiveCount = 0;
        self.sendCount = 0;
        self.receiveUpdateSignal.emit(None)

    def MoveToCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def errorHint(self, str):
        QMessageBox.information(self, str, str)

    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Sure To Quit?',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.com.close()
            self.receiveProgressStop = True
            self.programExitSaveParameters()
            event.accept()
        else:
            event.ignore()

    def findSerialPort(self):
        self.port_list = list(serial.tools.list_ports.comports())
        return self.port_list

    def portChanged(self):
        self.serialPortCombobox.setCurrentIndex(0)
        self.serialPortCombobox.setToolTip(str(self.portList[0]))

    def detectSerialPort(self):
        if not self.isDetectSerialPort:
            self.isDetectSerialPort = True
            t = threading.Thread(target=self.detectSerialPortProcess)
            t.setDaemon(True)
            t.start()

    def showCombobox(self):
        self.serialPortCombobox.showPopup()

    def detectSerialPortProcess(self):
        while (1):
            portList = self.findSerialPort()
            if len(portList) > 0:
                currText = self.serialPortCombobox.currentText()
                self.serialPortCombobox.clear()
                for i in portList:
                    showStr = str(i[0]) + " " + str(i[1])
                    if i[0].startswith("/dev/cu.Bluetooth-Incoming-Port"):
                        continue
                    self.serialPortCombobox.addItem(showStr)
                index = self.serialPortCombobox.findText(currText)
                if index >= 0:
                    self.serialPortCombobox.setCurrentIndex(index)
                else:
                    self.serialPortCombobox.setCurrentIndex(0)
                break
            time.sleep(1)
        self.showSerialComboboxSignal.emit()
        self.isDetectSerialPort = False

    def sendHistoryFindDelete(self, str):
        self.sendHistory.removeItem(self.sendHistory.findText(str))

    def asciiB2HexString(self, strB):
        strHex = binascii.b2a_hex(strB).upper()
        return re.sub(r"(?<=\w)(?=(?:\w\w)+$)", " ", strHex.decode()) + " "

    def hexStringB2Hex(self, hexString):
        dataList = hexString.split(" ")
        j = 0
        for i in dataList:
            if len(i) > 2:
                return -1
            elif len(i) == 1:
                dataList[j] = "0" + i
            j += 1
        data = "".join(dataList)
        try:
            data = bytes.fromhex(data)
        except Exception:
            return -1
        # print(data)
        return data

    def programExitSaveParameters(self):
        paramObj = parameters.ParametersToSave()
        paramObj.baudRate = self.serailBaudrateCombobox.currentIndex()
        paramObj.dataBytes = self.serailBytesCombobox.currentIndex()
        paramObj.parity = self.serailParityCombobox.currentIndex()
        paramObj.stopBits = self.serailStopbitsCombobox.currentIndex()
        paramObj.skin = self.param.skin
        if self.receiveSettingsHex.isChecked():
            paramObj.receiveAscii = False
        if not self.receiveSettingsAutoLinefeed.isChecked():
            paramObj.receiveAutoLinefeed = False
        else:
            paramObj.receiveAutoLinefeed = True
        paramObj.receiveAutoLindefeedTime = self.receiveSettingsAutoLinefeedTime.text()
        if self.sendSettingsHex.isChecked():
            paramObj.sendAscii = False
        if not self.sendSettingsScheduledCheckBox.isChecked():
            paramObj.sendScheduled = False
        paramObj.sendScheduledTime = self.sendSettingsScheduled.text()
        if not self.sendSettingsCFLF.isChecked():
            paramObj.useCRLF = False
        paramObj.sendHistoryList.clear()
        for i in range(0, self.sendHistory.count()):
            paramObj.sendHistoryList.append(self.sendHistory.itemText(i))
        if self.checkBoxRts.isChecked():
            paramObj.rts = 1
        else:
            paramObj.rts = 0
        if self.checkBoxDtr.isChecked():
            paramObj.dtr = 1
        else:
            paramObj.dtr = 0
        paramObj.encodingIndex = self.encodingCombobox.currentIndex()
        f = open(parameters.configFilePath, "wb")
        f.truncate()
        pickle.dump(paramObj, f)
        pickle.dump(paramObj.sendHistoryList, f)
        f.close()

    def programStartGetSavedParameters(self):
        paramObj = parameters.ParametersToSave()
        useDefultConfig = False
        if not useDefultConfig:
            try:
                f = open(parameters.configFilePath, "rb")
                paramObj = pickle.load(f)
                paramObj.sendHistoryList = pickle.load(f)
                f.close()
            except Exception as e:
                f = open(parameters.configFilePath, "wb")
                f.close()

        self.serailBaudrateCombobox.setCurrentIndex(paramObj.baudRate)
        self.serailBytesCombobox.setCurrentIndex(paramObj.dataBytes)
        self.serailParityCombobox.setCurrentIndex(paramObj.parity)
        self.serailStopbitsCombobox.setCurrentIndex(paramObj.stopBits)
        if paramObj.receiveAscii == False:
            self.receiveSettingsHex.setChecked(True)
        if paramObj.receiveAutoLinefeed == False:
            self.receiveSettingsAutoLinefeed.setChecked(False)
        else:
            self.receiveSettingsAutoLinefeed.setChecked(True)
        self.receiveSettingsAutoLinefeedTime.setText(paramObj.receiveAutoLindefeedTime)
        if paramObj.sendAscii == False:
            self.sendSettingsHex.setChecked(True)
        if paramObj.sendScheduled == False:
            self.sendSettingsScheduledCheckBox.setChecked(False)
        else:
            self.sendSettingsScheduledCheckBox.setChecked(True)
        self.sendSettingsScheduled.setText(paramObj.sendScheduledTime)
        if paramObj.useCRLF == False:
            self.sendSettingsCFLF.setChecked(False)
        else:
            self.sendSettingsCFLF.setChecked(True)
        for i in range(0, len(paramObj.sendHistoryList)):
            str = paramObj.sendHistoryList[i]
            self.sendHistory.addItem(str)
        if paramObj.rts == 0:
            self.checkBoxRts.setChecked(False)
        else:
            self.checkBoxRts.setChecked(True)
        if paramObj.dtr == 0:
            self.checkBoxDtr.setChecked(False)
        else:
            self.checkBoxDtr.setChecked(True)
        self.encodingCombobox.setCurrentIndex(paramObj.encodingIndex)
        self.param = paramObj

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.keyControlPressed = True
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.keyControlPressed:
                self.sendData()
        elif event.key() == Qt.Key_L:
            if self.keyControlPressed:
                self.sendArea.clear()
        elif event.key() == Qt.Key_K:
            if self.keyControlPressed:
                self.receiveArea.clear()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.keyControlPressed = False

    def sendAreaFontChanged(self, font):
        print("font changed")

    def functionAdd(self):
        QMessageBox.information(self, "On the way", "On the way")

    def showHideSettings(self):
        if self.isHideSettings:
            self.showSettings()
            self.isHideSettings = False
        else:
            self.hideSettings()
            self.isHideSettings = True

    def showSettings(self):
        self.settingWidget.show()
        self.settingsButton.setStyleSheet(
            parameters.strStyleShowHideButtonLeft.replace("$DataPath", self.DataPath))

    def hideSettings(self):
        self.settingWidget.hide()
        self.settingsButton.setStyleSheet(
            parameters.strStyleShowHideButtonRight.replace("$DataPath", self.DataPath))

    def showHideFunctional(self):
        if self.isHideFunctinal:
            self.showFunctional()
            self.isHideFunctinal = False
        else:
            self.hideFunctional()
            self.isHideFunctinal = True

    def showFunctional(self):
        self.functionalWiget.show()
        self.functionalButton.setStyleSheet(
            parameters.strStyleShowHideButtonRight.replace("$DataPath", self.DataPath))

    def hideFunctional(self):
        self.functionalWiget.hide()
        self.functionalButton.setStyleSheet(
            parameters.strStyleShowHideButtonLeft.replace("$DataPath", self.DataPath))

    def skinChange(self):
        if self.param.skin == 1:  # light
            file = open(self.DataPath + '/assets/qss/style-dark.qss', "r")
            self.param.skin = 2
        else:  # elif self.param.skin == 2: # dark
            file = open(self.DataPath + '/assets/qss/style.qss', "r")
            self.param.skin = 1
        self.app.setStyleSheet(file.read().replace("$DataPath", self.DataPath))

    def debugClick(self):
        if self.receiveArea.isVisible():
            self.receiveArea.hide()
            self.sendArea.hide()
            self.sendButtion.hide()
            self.clearReceiveButtion.hide()
        else:
            self.receiveArea.show()
            self.sendArea.show()
            self.sendButtion.show()
            self.clearReceiveButtion.hide()

    def showAbout(self):
        QMessageBox.information(self, "About", "<h1 style='color:#f75a5a';margin=10px;>" + parameters.appName +
                                '</h1><br><b style="color:#08c7a1;margin = 5px;">V' + str(
            helpAbout.versionMajor) + "." +
                                str(helpAbout.versionMinor) + "." + str(helpAbout.versionDev) +
                                "</b><br><br>" + helpAbout.date + "<br><br>" + helpAbout.strAbout())

    def selectFile(self):
        oldPath = self.filePathWidget.text()
        if oldPath == "":
            oldPath = os.getcwd()
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                                                "SelectFile",
                                                                oldPath,
                                                                "All Files (*);;")

        if fileName_choose == "":
            return
        self.filePathWidget.setText(fileName_choose)

    def sendFile(self):
        filename = self.filePathWidget.text()
        if not os.path.exists(filename):
            self.errorSignal.emit("File path error\npath:%s" % (filename))
            return
        try:
            f = open(filename, "rb")
        except Exception as e:
            self.errorSignal.emit("Open file %s failed! \n %s" % (filename, str(e)))
            return
        self.com.write(f.read())  # TODO: optimize send in new thread
        f.close()

    def clearHistory(self):
        self.param.sendHistoryList.clear()
        self.sendHistory.clear()
        self.errorSignal.emit("History cleared!")

    def autoUpdateDetect(self):
        auto = autoUpdate.AutoUpdate()
        if auto.detectNewVersion():
            auto.OpenBrowser()

    def openDevManagement(self):
        os.system('start devmgmt.msc')

    # def openWaveDisplay(self):
    #     self.wave = Wave()
    #     self.isWaveOpen = True
    #     self.wave.closed.connect(self.OnWaveClosed)
    #
    # def OnWaveClosed(self):
    #     print("wave window closed")
    #     self.isWaveOpen = False


def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow(app)
    print("data path:" + mainWindow.DataPath)
    print(mainWindow.param.skin)
    if (mainWindow.param.skin == 1):  # light skin
        file = open(mainWindow.DataPath + '/assets/qss/style.qss', "r")
    else:  # elif mainWindow.param == 2: # dark skin
        file = open(mainWindow.DataPath + '/assets/qss/style-dark.qss', "r")
    qss = file.read().replace("$DataPath", mainWindow.DataPath)
    app.setStyleSheet(qss)
    mainWindow.detectSerialPort()
    t = threading.Thread(target=mainWindow.autoUpdateDetect)
    t.setDaemon(True)
    t.start()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
