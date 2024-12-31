
import logging;
import sys;

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QListView, QListWidget;
from PyQt6 import uic, QtGui, QtCore;
from PyQt6.QtCore import pyqtSignal, Qt, QCoreApplication, QDir, QSettings, QTimer, QDateTime, QFile;

#from converterWorker import ConverterWorker;


class ControlCenterWindow(QMainWindow):

    mCounterCsv      = 0;
    mCounterSqlite   = 0;
    mCounterMsSql    = 0;
    mCounterPostgre  = 0;

    MsSqlHelper      = None;
    PostgreSqlHelper = None;
    SqliteHelper     = None;


    def __init__(self, parent=None):
        super(ControlCenterWindow, self).__init__(parent);

        self.originalPalette = QApplication.palette();
        uic.loadUi('main.ui', self);
        # ===================================== Загрузка настроек из файла ===================================== #
        self.loadSettings();
        self.loadPositionSizeMainWindow();

        # ===================================== Обработчики нажатия кнопок ===================================== #
        self.btnStartSqliteConverter.clicked.connect(self.StartSqliteConverterClicked);
        self.btnStartMsSqlConverter.clicked.connect(self.StartMsSqlConverterClicked);
        self.btnStartPostgreSqlConverter.clicked.connect(self.StartPostgreSqlConverterClicked);
        
        self.btnSaveSettings.clicked.connect(self.btnStartConverterClicked);
        self.btnStopConverter.clicked.connect(self.btnStartConverterClicked);

        # ===================================== Обработчики нажатия кнопок ===================================== #
        self.mConverterWorker = None;
        self.mConverterThread = None;



    def closeEvent(self, event):
        # Слот обрабатывает нажатие крестика в окне
        reply = QMessageBox.question(
            self, 
            'Информация',
            'Вы уверены, что хотите закрыть программу?',
             QMessageBox.StandardButton.Yes,
             QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.savePositionSizeMainWindow();
            event.accept();
        else:
            event.ignore();


    def fillDirectoryListView(self):
        model = QtGui.QStandardItemModel();
        #QtGui.QItemSelectionModel 
        self.DirectoryListView.setModel(model);

        curtDirSt = QDir.toNativeSeparators(QDir.currentPath());
        curDir = QDir(curtDirSt);
        curDir.setNameFilters(["*.csv"]);
        for entry in curDir.entryInfoList():
            item = QtGui.QStandardItem(entry.fileName());
            model.appendRow(item);
            #entry.canonicalFilePath();
            #entry.canonicalPath();


    def createSettingObject(self):
        curDir = QDir.toNativeSeparators(QDir.currentPath());
        settings = QSettings( curDir + "\settings.ini", QSettings.Format.IniFormat);
        return settings;


    def savePositionSizeMainWindow(self):
        settings = self.createSettingObject();
        settings.beginGroup("PositionSize");
        settings.setValue("PosX", self.x());
        settings.setValue("PosY", self.y());
        settings.setValue("Height", self.height());
        settings.setValue("Width", self.width());
        settings.endGroup();


    def loadPositionSizeMainWindow(self):
        settings = self.createSettingObject();
        settings.beginGroup("PositionSize");
        x = int(settings.value("PosX", 0));
        y = int(settings.value("PosY", 0));
        self.move(x, y);
        #self.resize(810, int(settings.value("Height", 810)));
        self.resize(810, 400);
        settings.endGroup();


    def saveSettings(self):
        settings = self.createSettingObject();
        settings.beginGroup("InitCsv");
        settings.setValue("CsvFileName", self.CsvFileName.text());
        #settings.setValue("CsvIgnoreFisrtRow", self.FileNameDbSqLite.text());
        settings.setValue("CsvDelimiter", self.CsvDelimiter.text());
        settings.endGroup();

        settings.beginGroup("InitSqlite");
        settings.setValue("SqliteFileName", self.SqliteFileName.text());
        settings.setValue("SqliteFromServer", self.SqliteFromServer.text());
        settings.endGroup();

        settings.beginGroup("InitMsSql");
        settings.setValue("MsSqlServerName", self.MsSqlServerName.text());
        settings.setValue("MsSqlUserName", self.MsSqlUserName.text());
        settings.setValue("MsSqlUserPassword", self.MsSqlUserPassword.text());
        settings.setValue("MsSqlDatabaseName", self.MsSqlDatabaseName.text());
        settings.endGroup();

        settings.beginGroup("InitPostgreSql");
        settings.setValue("PostgreServerName", self.PostgreServerName.text());
        settings.setValue("PostgreUserName", self.PostgreUserName.text());
        settings.setValue("PostgreUserPassword", self.PostgreUserPassword.text());
        settings.setValue("PostgreDatabaseName", self.PostgreDatabaseName.text());
        settings.endGroup();


    def loadSettings(self):
        settings = self.createSettingObject();

        settings.beginGroup("InitCsv");
        self.CsvFileName.setText(settings.value("CsvFileName", ""));
        #settings.setValue("CsvIgnoreFisrtRow", self.FileNameDbSqLite.text());
        self.CsvDelimiter.setText(settings.value("CsvDelimiter", ";"));
        settings.endGroup();

        settings.beginGroup("InitSqlite");
        self.SqliteFileName.setText(settings.value("SqliteFileName", "basestation.db"));
        self.SqliteFromServer.addItem("postgre");
        self.SqliteFromServer.addItem("mssql");
        self.SqliteFromServer.setCurrentIndex(self.SqliteFromServer.count()-1);

        #self.SqliteFromServer.setText(settings.value("SqliteFromServer", "postgre"));
        settings.endGroup();

        settings.beginGroup("InitMsSql");
        self.MsSqlServerName.setText(settings.value("MsSqlServerName", "192.168.229.251"));
        self.MsSqlUserName.setText(settings.value("MsSqlUserName", "sa"));
        self.MsSqlUserPassword.setText(settings.value("MsSqlUserPassword", "050973"));
        self.MsSqlDatabaseName.setText(settings.value("MsSqlDatabaseName", "basestation"));
        settings.endGroup();

        settings.beginGroup("InitPostgreSql");
        self.PostgreServerName.setText(settings.value("PostgreServerName", "192.168.229.251"));
        self.PostgreUserName.setText(settings.value("PostgreUserName", "postgres"));
        self.PostgreUserPassword.setText(settings.value("PostgreUserPassword", "050973"));
        self.PostgreDatabaseName.setText(settings.value("PostgreDatabaseName", "basestation"));
        settings.endGroup();


    def btnSaveSettingsAppClicked(self, state):
        self.saveSettings();


    def StartSqliteConverterClicked(self, state):
        print("StartSqliteConverter");


    def StartMsSqlConverterClicked(self, state):
        print("StartMsSqlConverter");


    def StartPostgreSqlConverterClicked(self, state):
        print("StartPostgreSqlConverter");



    def btnStopConverterClicked(self, state):
        self.stopConverter();


    def btnStartConverterClicked(self, state):
        self.startConverter();


    def stopConverter(self):
        if self.mConverterWorker and self.mConverterWorker.mRunning:
            self.mConverterWorker.mRunning = False;
            self.mConverterThread.terminate();
            self.mConverterThread.quit();
            self.mConverterThread.wait();
            self.mConverterWorker = None;
            self.mConverterThread = None;


    def startConverter(self):
        self.stopConverter();

        self.mConverterThread = QtCore.QThread();
        self.mConverterWorker = ConverterWorker(CsvFileName = self.FileNameCsv.text(), 
                                                SqLiteFileName = self.FileNameDbSqLite.text(), 
                                                MsSqlServer = self.SourceBdServerIp.text(),
                                                MsSqlUser = self.SourceBdUserName.text(), 
                                                MsSqlPass = self.SourceBdPassword.text(),
                                                MsSqlDbName = self.SourceBdDatabaseName.text(),
                                                Delimiter = self.Delimiter.text());
        self.mConverterWorker.moveToThread(self.mConverterThread);

        self.mConverterWorker.mErrorSignal.connect(self.ErrorSignal);
        self.mConverterWorker.mBeginCalcRowsSignal.connect(self.BeginCalcRowsSignal);
        self.mConverterWorker.mEndCalcRowsSignal.connect(self.EndCalcRowsSignal)
        self.mConverterWorker.mHandleRowSignal.connect(self.HandleRowSignal);

        self.mConverterThread.started.connect(self.mConverterWorker.startWork);
        self.mConverterThread.start();



    def ErrorSignal(self, error : str):
        print(error);


    def BeginCalcRowsSignal(self):
        pass;
        #print("BeginCalcRowsSignal");
        

    def EndCalcRowsSignal(self, countRow : int):
        self.RowsLabel.setText(str(countRow));
        #print("EndCalcRowsSignal => ", countRow);


    def HandleRowSignal(self, currentRow : int, countRows : int):
        #print("HandleRowSignal => ", currentRow, countRows);
        self.RowLabel.setText(str(currentRow));






if __name__ == '__main__':
    app = QApplication(sys.argv);
    controlCenterWindow = ControlCenterWindow();
    controlCenterWindow.show();
    sys.exit(app.exec());
