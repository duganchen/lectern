#!/usr/bin/env python2

from sip import setapi
setapi("QDate", 2)
setapi("QDateTime", 2)
setapi("QTextStream", 2)
setapi("QTime", 2)
setapi("QVariant", 2)
setapi("QString", 2)
setapi("QUrl", 2)


from PyQt4.QtCore import QAbstractItemModel, QDir, QModelIndex, Qt, QUrl
from PyQt4.QtGui import (QAction, QApplication, QDesktopServices, QMainWindow,
        QMessageBox, QSplitter, QStyle, QToolBar, QTreeView)
from PyQt4.QtWebKit import QWebView
from lxml import etree
from mimetypes import guess_type
from os.path import basename, exists, isfile, join, realpath, splitext
import posixpath
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

        splitter = QSplitter()
        tocView = QTreeView()
        self.tocModel = TableOfContents()
        tocView.setModel(self.tocModel)
        splitter.addWidget(tocView)
        self.webView = QWebView(self)
        splitter.addWidget(self.webView)
        self.setCentralWidget(splitter)

        self.ebook_info = {}
        self.setWindowTitle('Lectern')

        toolBar = QToolBar(self)

        self.prevAction = QAction(self.style().standardIcon(
            QStyle.SP_ArrowBack), 'Go back', toolBar)
        self.prevAction.setEnabled(False)
        self.prevAction.triggered.connect(self.prevChapter)
        toolBar.addAction(self.prevAction)

        self.nextAction = QAction(self.style().standardIcon(
            QStyle.SP_ArrowForward), 'Go forward', toolBar)
        self.nextAction.setEnabled(False)
        self.nextAction.triggered.connect(self.nextChapter)
        toolBar.addAction(self.nextAction)

        self.addToolBar(toolBar)

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

        if not 'META-INF/container.xml' in names:
            ebook.close()
            QMessageBox.critical(self, 'Invalid EPUB', 'container.xml not '\
                    'found')
            return None

        container_tree = etree.parse(ebook.open('META-INF/container.xml'))
        rootfile = container_tree.xpath("//*[local-name() = 'rootfile']")
        if len(rootfile) == 0:
            ebook.close()
            QMessageBox.critical(self, 'Invalid EPUB', 'root not found in '\
                    'manifest')
            return None

        content_opf = rootfile[0].get('full-path')
        if content_opf is None:
            ebook.close()
            QMessageBox.critical(self, 'Invalid EPUB', 'content.opf not found')
            return None

        ebook_info['opf_root'] = posixpath.dirname(content_opf)

        tree = etree.parse(ebook.open(content_opf))
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

        ebook.extractall(ebook_info['temp_path'])
        ebook.close()
        ebook_info['index'] = 0
        url = join(ebook_info['temp_path'], ebook_info['opf_root'],
                ebook_info['chapters'][0])
        self.webView.setUrl(QUrl(url))
        if len(ebook_info['chapters']) > 1:
            self.nextAction.setEnabled(True)
        return ebook_info

    def prevChapter(self):
        index = self.ebook_info['index']
        chapters = self.ebook_info['chapters']
        if index > 0:
            index -= 1
            if index == 0:
                self.prevAction.setEnabled(False)
            url = join(self.ebook_info['temp_path'],
                    self.ebook_info['opf_root'], chapters[index])
            self.webView.setUrl(QUrl(url))
            self.ebook_info['index'] = index
            self.nextAction.setEnabled(True)

    def nextChapter(self):
        index = self.ebook_info['index']
        chapters = self.ebook_info['chapters']
        if index < len(chapters) - 1:
            index += 1
            if index == len(chapters) - 1:
                self.nextAction.setEnabled(False)
            url = join(self.ebook_info['temp_path'],
                    self.ebook_info['opf_root'], chapters[index])
            self.webView.setUrl(QUrl(url))
            self.ebook_info['index'] = index
            self.prevAction.setEnabled(True)

    def closeBook(self):
        if self.ebook_info is not None and 'temp_path' in self.ebook_info:
            if exists(self.ebook_info['temp_path']):
                rmtree(self.ebook_info['temp_path'])
        self.ebook_info = None

        self.prevAction.setEnabled(False)
        self.nextAction.setEnabled(False)

    def closeEvent(self, event):

        self.closeBook()
        super(Lectern, self).closeEvent(event)


class TableOfContents(QAbstractItemModel):

    def __init__(self, parent=None):
        super(TableOfContents, self).__init__(parent)
        self.__rootItem = NavPoint('', '')
        a = NavPoint('a', 'b')
        a.append(NavPoint('b', 'c'))
        self.__rootItem.append(a)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role != Qt.DisplayRole:
            return None
        item = index.internalPointer()
        return item.text

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.__rootItem
        else:
            parentItem = parent.internalPointer()

        try:
            return self.createIndex(row, column, parentItem[row])
        except IndexError:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parent

        if parentItem == self.__rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row, 0, parentItem)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.__rootItem
        else:
            parentItem = parent.internalPointer()

        return len(parentItem)


class NavPoint(object):

    def __init__(self, text, src):
        self.__children = []
        self.text = text
        self.src = src
        self.parent = None

    def __len__(self):
        return len(self.__children)

    def append(self, item):
        item.parent = self
        self.__children.append(item)

    def __getitem__(self, key):
        return self.__children[key]


if __name__ == '__main__':
    main()
