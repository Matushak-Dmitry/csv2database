
import logging;
import sys;

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QListView, QListWidget;
from PyQt6 import uic, QtGui, QtCore;
from PyQt6.QtCore import pyqtSignal, Qt, QCoreApplication, QDir, QSettings, QTimer, QDateTime, QFile;
from PyQt6.QtSql import QSqlDatabase;

from FileModel import FileListModel;

#from ConverterPostgreWorker import ConverterPostgreWorker;
#from ConverterMsSqlWorker import ConverterMsSqlWorker;
from ConverterSqlitelWorker import ConverterSqliteWorker;
from FileModel import FileListModel;




class ControlCenterWindow(QMainWindow):

    mCounterCsv      = 0;
    mCounterSqlite   = 0;
    mCounterMsSql    = 0;
    mCounterPostgre  = 0;

    MsSqlHelper     = None;
    PostgreHelper   = None;
    SqLiteHelper    = None;
    mFileList       = [];

    mFieldsPosition = {};



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
        #self.DirectoryListView.currentChanged.connect(lambda: self.FileNameCsv.setText("Item Changed Signal"));

        self.mRootPath = QDir.toNativeSeparators(QDir.currentPath());
        rootDir = QDir(self.mRootPath);
        self.mBasePath = self.mRootPath + QDir.separator() + "storage";
        self.mCsvPath  = self.mRootPath + QDir.separator() + "csv";
        rootDir.mkpath(self.mBasePath);
        rootDir.mkpath(self.mCsvPath);

        model = FileListModel(self);
        model.setDirPath(self.mCsvPath);
        self.DirectoryListView.setModel(model);
        self.DirectoryListView.selectionModel().selectionChanged.connect(self.onDirectoryListViewItemChange);


        # ===================================== Обработчики нажатия кнопок ===================================== #
        self.mConverterWorker = None;
        self.mConverterThread = None;
        self.revisionDrivers();


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


    def revisionDrivers(self):
        db = QSqlDatabase.addDatabase('QSQLITE', "testing_Sqlite_connection"); 
        self.mDriverSqliteValid = db.isValid();
        if self.mDriverSqliteValid:
            print("Driver Sqlite is available.");
        else:
            print("Driver Sqlite is not available.");
        db = None;

        db = QSqlDatabase.addDatabase("QPSQL", "testing_Postgre_connection"); 
        self.mDriverPostgreValid = db.isValid();
        if self.mDriverPostgreValid:
            print("Driver Postgre SQL is available.")
        else:
            print("Driver Postgre SQL is not available.")
        db = None;

        db = QSqlDatabase.addDatabase("QODBC", "testing_MsSql_connection"); 
        self.mDriverMsSqlValid = db.isValid();
        if self.mDriverMsSqlValid:
            print("Driver Microsoft SQL is available.")
        else:
            print("Driver Microsoft SQL is not available.")
        db = None;


    def onDirectoryListViewItemChange(self, item):
        self.CsvFileName.setText(item.indexes()[0].data());


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

        settings.beginGroup("FieldsPosition");
        self.mFieldsPosition["bs_operator"]       = int(settings.value("bs_operator", -1));
        self.mFieldsPosition["bs_operator_id"]    = int(settings.value("bs_operator_id", -1));
        self.mFieldsPosition["bs_work_start"]     = int(settings.value("bs_work_start", -1));
        self.mFieldsPosition["bs_work_end"]       = int(settings.value("bs_work_end", -1));
        self.mFieldsPosition["bs_address_nostr"]  = int(settings.value("bs_address_nostr", -1));
        self.mFieldsPosition["bs_sector_ids"]     = int(settings.value("bs_sector_ids", -1));
        self.mFieldsPosition["bs_aft_param"]      = int(settings.value("bs_aft_param", -1));
        self.mFieldsPosition["bs_network_type"]   = int(settings.value("bs_network_type", -1));
        self.mFieldsPosition["bs_address_str"]    = int(settings.value("bs_address_str", -1));
        self.mFieldsPosition["bs_geo_lat"]        = int(settings.value("bs_geo_lat", -1));
        self.mFieldsPosition["bs_geo_lon"]        = int(settings.value("bs_geo_lon", -1));
        self.mFieldsPosition["bs_geo_type"]       = int(settings.value("bs_geo_type", -1));
        self.mFieldsPosition["bs_place_type"]     = int(settings.value("bs_place_type", -1));
        self.mFieldsPosition["bs_id"]             = int(settings.value("bs_id", -1));
        self.mFieldsPosition["bs_sector_id"]      = int(settings.value("bs_sector_id", -1));
        self.mFieldsPosition["bs_lac"]            = int(settings.value("bs_lac", -1));
        self.mFieldsPosition["bs_cell"]           = int(settings.value("bs_cell", -1));
        self.mFieldsPosition["bs_fone_id_cell"]   = int(settings.value("bs_fone_id_cell", -1));
        self.mFieldsPosition["bs_azimut"]         = int(settings.value("bs_azimut", -1));
        self.mFieldsPosition["bs_angle"]          = int(settings.value("bs_angle", -1));
        self.mFieldsPosition["bs_uklon_angle"]    = int(settings.value("bs_uklon_angle", -1));
        self.mFieldsPosition["bs_power"]          = int(settings.value("bs_power", -1));
        self.mFieldsPosition["bs_freq"]           = int(settings.value("bs_freq", -1));
        self.mFieldsPosition["bs_height"]         = int(settings.value("bs_height", -1));
        self.mFieldsPosition["bs_power_koef"]     = int(settings.value("bs_power_koef", -1));
        self.mFieldsPosition["bs_polariz"]        = int(settings.value("bs_polariz", -1));
        self.mFieldsPosition["bs_position_type"]  = int(settings.value("bs_position_type", -1));
        self.mFieldsPosition["bs_width_diagram"]  = int(settings.value("bs_width_diagram", -1));
        self.mFieldsPosition["bs_generation"]     = int(settings.value("bs_generation", -1));
        self.mFieldsPosition["bs_controller_num"] = int(settings.value("bs_controller_num", -1));
        self.mFieldsPosition["bs_BCC_NCC"]        = int(settings.value("bs_BCC_NCC", -1));
        self.mFieldsPosition["bs_type"]           = int(settings.value("bs_type", -1));
        self.mFieldsPosition["bs_freq_class"]     = int(settings.value("bs_freq_class", -1));
        self.mFieldsPosition["bs_name"]           = int(settings.value("bs_name", -1));
        self.mFieldsPosition["bs_channel"]        = int(settings.value("bs_channel", -1));
        self.mFieldsPosition["bs_freq_down"]      = int(settings.value("bs_freq_down", -1));
        self.mFieldsPosition["bs_freq_top"]       = int(settings.value("bs_freq_top", -1));
        self.mFieldsPosition["bs_level_side"]     = int(settings.value("bs_level_side", -1));
        self.mFieldsPosition["bs_cell_wimax"]     = int(settings.value("bs_cell_wimax", -1));
        self.mFieldsPosition["bs_mac"]            = int(settings.value("bs_mac", -1));
        settings.endGroup();



    def btnSaveSettingsAppClicked(self, state):
        self.saveSettings();


    def StartSqliteConverterClicked(self, state):
        self.startConverter("sqlite");


    def StartMsSqlConverterClicked(self, state):
        self.startConverter("mssql");


    def StartPostgreSqlConverterClicked(self, state):
        self.startConverter("postgre");


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


    def startConverter(self, clickName = "sqlite"):
        self.stopConverter();

        self.mConverterThread = QtCore.QThread();
        self.mConverterWorker = ConverterSqliteWorker(CsvFileName = self.FileNameCsv.text(),
                                                Delimiter = self.Delimiter.text(),
                                                SqLiteFileName = self.FileNameDbSqLite.text(), 
                                                MsSqlServer = self.SourceBdServerIp.text(),
                                                MsSqlUser = self.SourceBdUserName.text(), 
                                                MsSqlPass = self.SourceBdPassword.text(),
                                                MsSqlDbName = self.SourceBdDatabaseName.text(),

                                                );
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
