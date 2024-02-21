# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'light.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1315, 720)
        MainWindow.setMinimumSize(QtCore.QSize(1280, 720))
        font = QtGui.QFont()
        font.setFamily("等线")
        font.setPointSize(16)
        MainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setMinimumSize(QtCore.QSize(1280, 720))
        self.centralwidget.setObjectName("centralwidget")
        self.sidewidget = QtWidgets.QWidget(self.centralwidget)
        self.sidewidget.setGeometry(QtCore.QRect(0, 0, 60, 720))
        self.sidewidget.setMaximumSize(QtCore.QSize(60, 16777215))
        self.sidewidget.setObjectName("sidewidget")
        self.stackedWidget = QtWidgets.QStackedWidget(self.sidewidget)
        self.stackedWidget.setGeometry(QtCore.QRect(0, 0, 60, 720))
        self.stackedWidget.setStyleSheet("background-color: white;")
        self.stackedWidget.setObjectName("stackedWidget")
        self.page = QtWidgets.QWidget()
        self.page.setObjectName("page")
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName("page_2")
        self.pushButton = QtWidgets.QPushButton(self.page_2)
        self.pushButton.setGeometry(QtCore.QRect(5, 20, 50, 50))
        self.pushButton.setStyleSheet("QPushButton\n"
"{\n"
"background-color: transparent;\n"
"border-radius:31px;\n"
"border-image: url(:/icon/unfold.png)\n"
"}\n"
"\n"
"QPushButton:pressed\n"
"{\n"
"border-image: url(:/icon/unfold_selected.png)\n"
"}")
        self.pushButton.setText("")
        self.pushButton.setObjectName("pushButton")
        self.stackedWidget.addWidget(self.page_2)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "短视频推荐系统"))
import resources_rc
