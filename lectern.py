#!/usr/bin/env python2

from sip import setapi
setapi("QDate", 2)
setapi("QDateTime", 2)
setapi("QTextStream", 2)
setapi("QTime", 2)
setapi("QVariant", 2)
setapi("QString", 2)
setapi("QUrl", 2)


from PyQt4.QtGui import (QApplication, QMainWindow, QMessageBox)
from PyQt4.QtWebKit import QWebView
from mimetypes import guess_type
from os.path import isfile, realpath
import sys
from zipfile import ZipFile


def main():
    app = QApplication(sys.argv)
    lectern = Lectern()
    lectern.show()
    sys.exit(app.exec_())


class Lectern(QMainWindow):

    def __init__(self, parent=None):
        super(Lectern, self).__init__(parent)
        self.webView = QWebView(self)
        self.setCentralWidget(self.webView)
        self.ebook = None

        try:
            self.openBook(QApplication.arguments()[1])
        except IndexError:
            pass

    def openBook(self, path):
        path = realpath(path)
        print path
        if not isfile(path):
            QMessageBox.critical(self, 'File not found', 'File not found')
            return None

        mimetype, _ = guess_type(path)
        if mimetype != 'application/epub+zip':
            QMessageBox.critical(self, 'Not an EPUB', 'Not an EPUB')
            return None

        self.ebook = ZipFile(path)

        names = self.ebook.namelist()
        if not 'content.opf' in names:
            QMessageBox.critical(self, 'Invalid EPUB', 'Invalid EPUB')

        print self.ebook.open('content.opf').read()

    def closeBook(self):
        if self.ebook is not None:
            self.ebook.close()
            self.ebook = None

    def closeEvent(self, event):

        print 'Closing'
        self.closeBook()
        super(Lectern, self).closeEvent(event)

if __name__ == '__main__':
    main()
