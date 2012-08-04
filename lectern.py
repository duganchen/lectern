#!/usr/bin/env python2

from sip import setapi
setapi("QDate", 2)
setapi("QDateTime", 2)
setapi("QTextStream", 2)
setapi("QTime", 2)
setapi("QVariant", 2)
setapi("QString", 2)
setapi("QUrl", 2)


from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QApplication, QMainWindow, QSplitter, QTreeView
from PyQt4.QtWebKit import QWebView
import sys


def main():
    app = QApplication(sys.argv)
    lectern = Lectern()
    lectern.show()
    sys.exit(app.exec_())


class Lectern(QMainWindow):

    def __init__(self, parent=None):
        super(Lectern, self).__init__(parent)
        splitter = QSplitter(self)
        splitter.addWidget(QTreeView())
        webView = QWebView(self)
        webView.setUrl(QUrl('http://duganchen.ca'))
        splitter.addWidget(webView)
        self.setCentralWidget(splitter)


if __name__ == '__main__':
    main()
