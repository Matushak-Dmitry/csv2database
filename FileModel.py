
from PyQt6.QtCore import pyqtSignal, QObject;
from PyQt6.QtGui import QStandardItemModel;


class FileModel(QStandardItemModel):

    def __init__(self, parent) -> None:
        super(FileModel).__init__(parent);