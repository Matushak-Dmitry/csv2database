
# поддержка SQL сервером функции size
# qDebug() << database.driver()->hasFeature(QSqlDriver::QuerySize);


# int rowsCount = 0;
# if (query.last()) 
# 	rowsCount = query.at() + 1;
# qDebug() << "query size:" << rowsCount;
#Чтобы вернуться в начало набора данных воспользуемся функциями first() и previous():
#query.first();
#query.previous(); 


from PyQt6 import QtCore;
from PyQt6.QtCore import pyqtSignal, QObject, QDir, QFile, QDateTime;
from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlDriver;


class ConverterSqliteWorker(QObject):

    mRunning = False;

    mErrorSignal              = pyqtSignal(str);
    mBeginCalcRowsSignal      = pyqtSignal();
    mEndCalcRowsSignal        = pyqtSignal(int);
    mHandleRowSignal          = pyqtSignal(int, int); # обработано, всего

    mLastError                = "";


    def __init__(self, parent = None, SqliteFileName = "", MsSqlServer = "", MsSqlUser = "", MsSqlPass = "", MsSqlDbName = ""):
        super(ConverterSqliteWorker, self).__init__(parent);

        self.SqliteFileName = SqliteFileName;
        self.MsSqlServer    = MsSqlServer;
        self.MsSqlUser      = MsSqlUser;
        self.MsSqlPass      = MsSqlPass;
        self.MsSqlDbName    = MsSqlDbName;

        self.mRecordCounter = 0;

        self.mRootPath = QDir.toNativeSeparators(QDir.currentPath());
        rootDir = QDir(self.mRootPath);
        self.mBasePath = self.mRootPath + QDir.separator() + "storage";
        self.mCsvPath  = self.mRootPath + QDir.separator() + "csv";
        rootDir.mkpath(self.mBasePath);
        rootDir.mkpath(self.mCsvPath);
        self.SqLiteBasePathAndName = self.mBasePath + QDir.separator() + self.SqliteFileName;



    def initSqLiteDatabase(self, reCreate : bool):
        if reCreate:
            SqLiteFile = QFile(self.SqLiteBasePathAndName);
            if SqLiteFile.exists():
                SqLiteFile.remove();

        self.mSqLiteDatabase = QSqlDatabase.addDatabase('QSQLITE');
        self.mSqLiteDatabase.setDatabaseName(self.SqLiteBasePathAndName);
        if not self.mSqLiteDatabase.open():
            self.mLastError = self.mSqLiteDatabase.lastError().text();
            print(f'Не удалось открыть базу данных: {self.mLastError}');
            self.mErrorSignal.emit("SqLite => " + self.mLastError);
            return False;

        self.mSqLiteQuery = QSqlQuery(self.mSqLiteDatabase);
        self.mSqLiteQuery.exec("""
            CREATE TABLE IF NOT EXISTS bs (
                operator TEXT,
                operator_id TEXT,
                cell TEXT,
                lac TEXT,
                lat REAL,
                lon REAL,
                azimut INTEGER,
                angle INTEGER,
                power TEXT,
                height TEXT,
                uklon TEXT,
                freq TEXT,
                freq_down TEXT,
                freq_top TEXT,
                address_str TEXT,
                address_nostr TEXT);
        """);
        if self.mSqLiteQuery.lastError().isValid():
            self.mLastError = self.mSqLiteQuery.lastError().text();
            print(f'Ошибка при создании таблицы: {self.mLastError}');
            self.mErrorSignal.emit("SqLite => " + self.mLastError);
            return;
        self.mSqLiteQuery.exec("""CREATE INDEX IF NOT EXISTS idx_cell_lac ON bs (cell, lac);""");
        if self.mSqLiteQuery.lastError().isValid():
            self.mLastError = self.mSqLiteQuery.lastError().text();
            print(f'Ошибка при создании индекса: {self.mLastError}');
            self.mErrorSignal.emit("SqLite => " + self.mLastError);
            return;
        self.mSqLiteDatabase.commit();
        print("Создание базы данных SqLite завершено успешно");

        if QSqlDatabase.contains("MsSql_" + self.MsSqlDbName):
            self.mMsSqlDatabase = QSqlDatabase.database("MsSql_" + self.MsSqlDbName);
        else:
            self.mMsSqlDatabase = QSqlDatabase.addDatabase("QODBC", "MsSql_" + self.MsSqlDbName);

        self.mConnectionString = "DRIVER={SQL Server};SERVER={%s};UID={%s};PWD={%s}" % (self.MsSqlServer, self.MsSqlUser, self.MsSqlPass);
        self.mMsSqlDatabase.setDatabaseName(self.mConnectionString);
        self.mMsSqlState = self.mMsSqlDatabase.open();
        if (not self.mMsSqlState):
            print(self.mMsSqlDatabase.lastError().text());
            #self.mErrorSignal.emit("MsSql => " + self.mMsSqlDatabase.lastError().text());
            return;
        self.mMsSqlQuery = QSqlQuery(self.mMsSqlDatabase);





    def startWork(self):
        self.mRunning = True;

        self.initSqLiteDatabase(True);
        self.mRecordCounter = 0;

        self.mBeginCalcRowsSignal.emit();
        self.mMsSqlQuery.exec(f"""
            USE {self.MsSqlDbName};
            SELECT COUNT(*) FROM bs_all_operators
            """);
        if self.mMsSqlQuery.lastError().isValid():
            self.mLastError = self.mMsSqlQuery.lastError().text();
            self.mRunning = False;
            print(f"SqLite MsSql => {self.mLastError}");
            self.mErrorSignal.emit(f"SqLite MsSql => {self.mLastError}");
            return;
        self.mMsSqlQuery.next();
        rowCount = self.mMsSqlQuery.value(0);
        self.mEndCalcRowsSignal.emit(rowCount);
        self.mMsSqlQuery.exec(f"""
            USE {self.MsSqlDbName};
            SELECT * FROM bs_all_operators
            """);
        if self.mMsSqlQuery.lastError().isValid():
            self.mLastError = self.mMsSqlQuery.lastError().text();
            self.mRunning = False;
            print(f"SqLite MsSql => {self.mLastError}");
            self.mErrorSignal.emit(f"SqLite MsSql => {self.mLastError}");
            return;


        self.mSqLiteQuery.prepare('''
                INSERT INTO bs (
                    operator,
                    operator_id,
                    cell,
                    lac,
                    lat,
                    lon,
                    azimut, angle, power, height,
                    uklon, freq, freq_down, freq_top, address_str, address_nostr                    
                )
                VALUES (
                    :operator,
                    :operator_id,
                    :cell,
                    :lac,
                    :lat,
                    :lon,
                    :azimut, 
                    :angle, 
                    :power, 
                    :height,
                    :uklon, 
                    :freq, 
                    :freq_down, 
                    :freq_top, 
                    :address_str, 
                    :address_nostr
                )''');

        self.mMsSqlQuery.first();
        while self.mMsSqlQuery.next():
            if (not self.mRunning):
                break;

            self.mSqLiteQuery.bindValue(':operator', self.mMsSqlQuery.value(0));
            self.mSqLiteQuery.bindValue(':operator_id', self.mMsSqlQuery.value(1));
            self.mSqLiteQuery.bindValue(':cell', self.mMsSqlQuery.value(16));
            self.mSqLiteQuery.bindValue(':lac', self.mMsSqlQuery.value(15));
            self.mSqLiteQuery.bindValue(':lat', self.mMsSqlQuery.value(9));
            self.mSqLiteQuery.bindValue(':lon', self.mMsSqlQuery.value(10));
            self.mSqLiteQuery.bindValue(':azimut', self.mMsSqlQuery.value(18));
            self.mSqLiteQuery.bindValue(':angle', self.mMsSqlQuery.value(19));
            self.mSqLiteQuery.bindValue(':power', self.mMsSqlQuery.value(21));
            self.mSqLiteQuery.bindValue(':height', self.mMsSqlQuery.value(23));
            self.mSqLiteQuery.bindValue(':uklon', self.mMsSqlQuery.value(20));
            self.mSqLiteQuery.bindValue(':freq', self.mMsSqlQuery.value(22));
            self.mSqLiteQuery.bindValue(':freq_down', self.mMsSqlQuery.value(35));
            self.mSqLiteQuery.bindValue(':freq_top', self.mMsSqlQuery.value(36));
            self.mSqLiteQuery.bindValue(':address_str', self.mMsSqlQuery.value(8));
            self.mSqLiteQuery.bindValue(':address_nostr', self.mMsSqlQuery.value(4));

            if not self.mSqLiteQuery.exec():
                self.mLastError = self.mSqLiteQuery.lastError().text();
                print(f'Ошибка при добавлении записи: {self.mLastError}')
                self.mErrorSignal.emit(f"SqLite => {self.mLastError}");
                self.mRunning = False;
                
            self.mRecordCounter += 1;
            if (self.mRecordCounter % 100) == 0:
                self.mHandleRowSignal.emit(self.mRecordCounter, rowCount);

        self.mRunning = False;
        self.mHandleRowSignal.emit(self.mRecordCounter, rowCount);
        self.mSqLiteDatabase.commit();









if __name__ == '__main__':
    print("Start main");
    converter = ConverterSqliteWorker(None, "basestation.db", "localhost", "sa", "050973", "basestation");
    converter.startWork();
