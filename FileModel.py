
from PyQt6.QtCore import QDir;
from PyQt6.QtGui import QStandardItem, QStandardItemModel;


class FileListModel(QStandardItemModel):


    def __init__(self, parent=None):
        super(FileListModel, self).__init__(parent)


    def setDirPath(self, path):
        curDir = QDir(path);
        curDir.setNameFilters(["*.csv"]);
        for entry in curDir.entryInfoList():
            item = QStandardItem(entry.fileName());
            self.appendRow(item);
