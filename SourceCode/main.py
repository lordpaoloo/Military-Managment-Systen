from UI import Ui_MainWindow    
import sys
from PyQt5.QtWidgets import QMainWindow,QApplication 
from PyQt5.QtGui import QIcon
import pymupdf

class MyMainWindow(QMainWindow,Ui_MainWindow):
        def __init__(self,parent=None):
                super(MyMainWindow,self).__init__(parent)
                self.setupUi(self)
                self.setWindowTitle("MMS")
                self.setWindowIcon(QIcon("icon.ico"))

if __name__ == "__main__":
        app=QApplication(sys.argv)
        myWin=MyMainWindow()
        myWin.show()
        sys.exit(app.exec_())   
        