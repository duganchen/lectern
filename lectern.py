#!/usr/bin/env python2

from sip import setapi
setapi("QDate", 2)
setapi("QDateTime", 2)
setapi("QTextStream", 2)
setapi("QTime", 2)
setapi("QVariant", 2)
setapi("QString", 2)
setapi("QUrl", 2)


from PyQt4.QtCore import QDir, QUrl
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
        self.ebook_info = {}

        try:
            self.ebook_info = self.openBook(QApplication.arguments()[1])
        except IndexError:
            pass

    def openBook(self, path):
        ebook_info = {}
        path = realpath(path)
        if not isfile(path):
            QMessageBox.critical(self, 'File not found', 'File not found')

        mimetype, _ = guess_type(path)
        if mimetype != 'application/epub+zip':
            QMessageBox.critical(self, 'Not an EPUB', 'Not an EPUB')
            return None

        ebook = ZipFile(path)

        names = ebook.namelist()
        if not 'content.opf' in names:
            ebook.close()
            QMessageBox.critical(self, 'Invalid EPUB', 'content.opf not found')
            return None

        tree = etree.parse(ebook.open('content.opf'))
        manifest = tree.xpath("*[local-name() = 'manifest']")
        if len(manifest) == 0:
            ebook.close()
            QMessageBox.critical(self, 'Invalid EPUB', 'Manifest not found')
            return None
        manifest = manifest[0]

        items = {}
        for item in manifest:
            item_id = item.get('id')
            if item_id is None:
                ebook.close()
                QMessageBox.critical(self, 'Invalid EPUB', 'Item has no id')
                return None

            href = item.get('href')
            if href is None:
                ebook.close()
                QMessageBox.critical(self, 'Invalid EPUB', 'Item has no href')
                return None

            items[item_id] = href

        spine = tree.xpath("*[local-name() = 'spine']")
        if len(spine) == 0:
            ebook.close()
            QMessageBox.critical(self, 'Invalid EPUB', 'Spine not found')
            return None
        spine = spine[0]

        ebook_info['chapters'] = []
        for itemref in spine:
            idref = itemref.get('idref')
            if not idref in items:
                ebook.close()
                QMessageBox.critical(self, 'Invalid EPUB', 'Item in spine '\
                        'not found in manifest')
                return None
            ebook_info['chapters'].append(items[idref])

        if len(ebook_info['chapters']) == 0:
            ebook.close()
            QMessageBox.critical(self, 'Invalid EPUB', 'Content not found')
            return None

        temp = QDir.toNativeSeparators(QDesktopServices.storageLocation(
            QDesktopServices.TempLocation))

        ebook_info['temp_path'] = join(temp, splitext(basename(path))[0])
        if exists(ebook_info['temp_path']):
            rmtree(ebook_info['temp_path'])

        ebook.extractall(ebook_info['temp_path'], items.values())
        ebook.close()
        ebook_info['index'] = 0
        url = join(ebook_info['temp_path'], ebook_info['chapters'][0])
        self.webView.setUrl(QUrl(url))
        return ebook_info

    def closeBook(self):
        if self.ebook_info is not None and 'temp_path' in self.ebook_info:
            if exists(self.ebook_info['temp_path']):
                rmtree(self.ebook_info['temp_path'])
        self.ebook_info = None

    def closeEvent(self, event):

        self.closeBook()
        super(Lectern, self).closeEvent(event)

if __name__ == '__main__':
    main()
