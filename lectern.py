#!/usr/bin/env python2

from sip import setapi
setapi("QDate", 2)
setapi("QDateTime", 2)
setapi("QTextStream", 2)
setapi("QTime", 2)
setapi("QVariant", 2)
setapi("QString", 2)
setapi("QUrl", 2)


from PyQt4.QtCore import QDir
from PyQt4.QtGui import (QApplication, QDesktopServices, QMainWindow,
        QMessageBox)
from PyQt4.QtWebKit import QWebView
from lxml import etree
from mimetypes import guess_type
from os.path import basename, exists, isfile, join, realpath, splitext
from shutil import rmtree
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
            QMessageBox.critical(self, 'Invalid EPUB', 'content.opf not found')
            return None

        tree = etree.parse(self.ebook.open('content.opf'))
        manifest = tree.xpath("*[local-name() = 'manifest']")
        if len(manifest) == 0:
            QMessageBox.critical(self, 'Invalid EPUB', 'Manifest not found')
            return None
        manifest = manifest[0]

        items = {}
        for item in manifest:
            item_id = item.get('id')
            if item_id is None:
                QMessageBox.critical(self, 'Invalid EPUB', 'Item has no id')
                return None

            href = item.get('href')
            if href is None:
                QMessageBox.critical(self, 'Invalid EPUB', 'Item has no href')

            items[item_id] = href

        spine = tree.xpath("*[local-name() = 'spine']")
        if len(spine) == 0:
            QMessageBox.critical(self, 'Invalid EPUB', 'Spine not found')
            return None
        spine = spine[0]

        chapters = []
        for itemref in spine:
            idref = itemref.get('idref')
            if not idref in items:
                QMessageBox.critical(self, 'Invalid EPUB', 'Item in spine '\
                        'not found in manifest')
            chapters.append(items[idref])

        temp = QDir.toNativeSeparators(QDesktopServices.storageLocation(
            QDesktopServices.TempLocation))

        temp = join(temp, splitext(basename(path))[0])
        if exists(temp):
            rmtree(temp)

        self.ebook.extractall(temp, items.values())

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
