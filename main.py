#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time

sys.path.insert(0, '/home/dave/QtProjects/Helpers')

from PyQt5 import QtGui, QtCore
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QTreeWidgetItem

import mainwindowui
from LocalMachines import LocalMachines
from KodiJson import KodiJson
from PyQt5OverrideCursor import QWaitCursor

class MyApplication(QApplication):
    def __init__(self, arguments):
        super(MyApplication, self).__init__(arguments)

        self.mainWindow = None

        self.setApplicationName('KodiControl')

class MyMainWindow(QMainWindow, mainwindowui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)

        self.actionQuit.triggered.connect(QApplication.instance().quit)

        self.localMachines = LocalMachines()
        self.kodiJson = None

        self.LoadLocalMachines()
        self.NewMachine(0)

        self.comboBox_SelectDevice.currentIndexChanged.connect(self.NewMachine)
        self.pushButton_Batch_Update.clicked.connect(self.onButton_Batch_Update)
        self.pushButton_Batch_ClearStatus.clicked.connect(self.onButton_Batch_ClearStatus)
        self.pushButton_Batch_PingVersion.clicked.connect(self.onButton_Batch_PingVersion)
        self.pushButton_Batch_SelectActive.clicked.connect(self.onButton_Batch_SelectActive)
        self.pushButton_Batch_SelectAll.clicked.connect(self.onButton_Batch_SelectAll)
        self.pushButton_Batch_SelectNone.clicked.connect(self.onButton_Batch_SelectNone)
        self.pushButton_Movies_List.clicked.connect(self.onButton_Movies_List)
        self.pushButton_Movies_Refresh.clicked.connect(self.onButton_Movies_Refresh)
        self.pushButton_Movies_SelectAll.clicked.connect(self.onButton_Movies_SelectAll)
        self.pushButton_Movies_SelectNone.clicked.connect(self.onButton_Movies_SelectNone)
        self.pushButton_SelectedDevice_Ping.clicked.connect(self.onButton_SelectedDevice_Ping)
        self.pushButton_SelectedDevice_Reboot.clicked.connect(self.onButton_SelectedDevice_Reboot)
        self.pushButton_SelectedDevice_Version.clicked.connect(self.onButton_SelectedDevice_Version)
        self.pushButton_SelectedDevice_VideoClean.clicked.connect(self.onButton_SelectedDevice_VideoClean)
        self.pushButton_SelectedDevice_VideoUpdate.clicked.connect(self.onButton_SelectedDevice_VideoUpdate)
        self.pushButton_TV_List.clicked.connect(self.onButton_TV_List)
        self.pushButton_TV_Refresh.clicked.connect(self.onButton_TV_Refresh)
        self.pushButton_TV_RefreshAll.clicked.connect(self.onButton_TV_RefreshAll)
        self.pushButton_TV_SelectAll.clicked.connect(self.onButton_TV_SelectAll)
        self.pushButton_TV_SelectNone.clicked.connect(self.onButton_TV_SelectNone)

    def LoadLocalMachines(self):
        """Load the local machines into the combo box."""

        data = []

        for key in self.localMachines.LOCAL_MACHINES.keys():
            lm = self.localMachines.LOCAL_MACHINES[key]
            data.append((lm.description, lm.active, key))

        data.sort()
        for (description, active, key) in data:
            self.comboBox_SelectDevice.addItem(description, key)

            itm = QTreeWidgetItem(self.treeWidget_BatchUpdate, [str(key), description, ''])
            itm.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            if (active):
                itm.setCheckState(1, Qt.Checked)
            else:
                itm.setCheckState(1, Qt.Unchecked)

        self.treeWidget_BatchUpdate.setColumnHidden(0, True)
        self.treeWidget_BatchUpdate.resizeColumnToContents(1)
        self.treeWidget_BatchUpdate.setColumnWidth(1, self.treeWidget_BatchUpdate.columnWidth(1) + 20)

    def onButton_Batch_ClearStatus(self):
        """Clear the 'status' column in self.treeWidget_BatchUpdate."""

        with QWaitCursor():
            for index in range(self.treeWidget_BatchUpdate.topLevelItemCount()):
                self.treeWidget_BatchUpdate.topLevelItem(index).setData(2, Qt.DisplayRole, '')

        self.treeWidget_BatchUpdate.scrollToItem(self.treeWidget_BatchUpdate.topLevelItem(0))

        QApplication.instance().beep()

    def onButton_Batch_PingVersion(self):
        """Update the selected devices from the self.treeWidget_BatchUpdate."""

        with QWaitCursor():
            for index in range(self.treeWidget_BatchUpdate.topLevelItemCount()):
                itm = self.treeWidget_BatchUpdate.topLevelItem(index)
                self.treeWidget_BatchUpdate.setCurrentItem(itm)
                self.treeWidget_BatchUpdate.repaint()

                if (itm.checkState(1) != Qt.Checked):
                    time.sleep(0.5)
                    continue

                key = int(itm.data(0, Qt.DisplayRole))
                lm = self.localMachines.LOCAL_MACHINES[key]
                kj = KodiJson(lm.ipAddress, lm.port, lm.userId, lm.password, lm.description)

                self.SetBatchUpdateStatus(itm, 'Pinging {}...'.format(lm.ipAddress))
                response = kj.ping()
                if (response != 'pong'):
                    self.SetBatchUpdateStatus(itm, response)
                    continue

                kodiVersion = self.kodiJson.ApplicationVersion()
                if (type(kodiVersion) is str):
                    self.SetBatchUpdateStatus(itm, kodiVersion)
                    continue

                jsonrpcVersion = self.kodiJson.JSONRPCVersion()
                if (type(jsonrpcVersion) is str):
                    self.SetBatchUpdateStatus(itm, jsonrpcVersion)
                    continue

                s = 'Kodi Version: {}.{}.{} ({}); JSONRPC Version: {}.{}.{}'.format(
                    kodiVersion['major'], kodiVersion['minor'], kodiVersion['revision'], kodiVersion['tag'],
                    jsonrpcVersion['major'], jsonrpcVersion['minor'], jsonrpcVersion['patch'])
                self.SetBatchUpdateStatus(itm, s)

        self.treeWidget_BatchUpdate.setCurrentItem(self.treeWidget_BatchUpdate.topLevelItem(0))

        QApplication.instance().beep()

    def onButton_Batch_SelectActive(self):
        """Select all of the 'active' devices listed in self.treeWidget_BatchUpdate."""

        if (self.treeWidget_BatchUpdate.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'Batch Update Devices List Is Empty',
                'The batch update devices list is empty.  Unable to continue.')
            return

        with QWaitCursor():
            for index in range(self.treeWidget_BatchUpdate.topLevelItemCount()):

                key = int(self.treeWidget_BatchUpdate.topLevelItem(index).data(0, Qt.DisplayRole))
                lm = self.localMachines.LOCAL_MACHINES[key]

                if (lm.active):
                    self.treeWidget_BatchUpdate.topLevelItem(index).setCheckState(1, Qt.Checked)
                else:
                    self.treeWidget_BatchUpdate.topLevelItem(index).setCheckState(1, Qt.Unchecked)

        self.treeWidget_BatchUpdate.scrollToItem(self.treeWidget_BatchUpdate.topLevelItem(0))

        QApplication.instance().beep()

    def onButton_Batch_SelectAll(self):
        """Select all of the devices listed in self.treeWidget_BatchUpdate."""

        if (self.treeWidget_BatchUpdate.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'Batch Update Devices List Is Empty',
                'The batch update devices list is empty.  Unable to continue.')
            return

        with QWaitCursor():
            for index in range(self.treeWidget_BatchUpdate.topLevelItemCount()):
                self.treeWidget_BatchUpdate.topLevelItem(index).setCheckState(1, Qt.Checked)

        self.treeWidget_BatchUpdate.scrollToItem(self.treeWidget_BatchUpdate.topLevelItem(0))

        QApplication.instance().beep()

    def onButton_Batch_SelectNone(self):
        """Un-select all of the devices listed in self.treeWidget_BatchUpdate."""

        if (self.treeWidget_BatchUpdate.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'Batch Update Devices List Is Empty',
                'The batch update devices list is empty.  Unable to continue.')
            return

        with QWaitCursor():
            for index in range(self.treeWidget_BatchUpdate.topLevelItemCount()):
                self.treeWidget_BatchUpdate.topLevelItem(index).setCheckState(1, Qt.Unchecked)

        self.treeWidget_BatchUpdate.scrollToItem(self.treeWidget_BatchUpdate.topLevelItem(0))

        QApplication.instance().beep()

    def onButton_Batch_Update(self):
        """Update the selected devices from the self.treeWidget_BatchUpdate."""

        with QWaitCursor():
            for index in range(self.treeWidget_BatchUpdate.topLevelItemCount()):
                itm = self.treeWidget_BatchUpdate.topLevelItem(index)
                self.treeWidget_BatchUpdate.setCurrentItem(itm)
                self.treeWidget_BatchUpdate.repaint()

                if (itm.checkState(1) != Qt.Checked):
                    time.sleep(0.5)
                    continue

                key = int(itm.data(0, Qt.DisplayRole))
                lm = self.localMachines.LOCAL_MACHINES[key]
                kj = KodiJson(lm.ipAddress, lm.port, lm.userId, lm.password, lm.description)

                response = kj.ping()
                if (response != 'pong'):
                    self.SetBatchUpdateStatus(itm, response)
                    continue

                self.SetBatchUpdateStatus(itm, 'Updating...')

                kj.WakeUp(10.0)
                response = kj.GetInfoBooleans('Library.IsScanningVideo')
                if (type(response) is not dict):
                    self.SetBatchUpdateStatus(itm, response)
                    continue

                if (not response['Library.IsScanningVideo']):
                    response = kj.VideoLibraryScan()
                    if (response != u'OK'):
                        self.SetBatchUpdateStatus(itm, response)
                        continue

                time.sleep(10.0)

                response = kj.GetInfoBooleans('Library.IsScanningVideo')
                if (type(response) is not dict):
                    self.SetBatchUpdateStatus(itm, response)
                    continue

                while (response['Library.IsScanningVideo']):
                    time.sleep(1.0)

                    response = kj.GetInfoBooleans('Library.IsScanningVideo')
                    if (type(response) is not dict):
                        self.SetBatchUpdateStatus(itm, response)
                        break

                self.SetBatchUpdateStatus(itm, 'Update complete!')

        self.treeWidget_BatchUpdate.setCurrentItem(self.treeWidget_BatchUpdate.topLevelItem(0))

        QApplication.instance().beep()

    def onButton_Movies_List(self):
        """Get a list of the movies on the selecte machine and display them."""

        waitCursor = QWaitCursor()
        self.treeWidget_Movies.clear()
        self.treeWidget_Movies.resetIndentation()
        response = self.kodiJson.VideoLibraryGetMovies()

        if (type(response) is str):
            del waitCursor
            QApplication.instance().beep()
            QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))
            return

        self.statusBar.showMessage('{} movies found.'.format(len(response)), 15000)

        for movie in response:
            itm = QTreeWidgetItem(self.treeWidget_Movies, [str(movie['movieid']), movie['label'], str(movie['year'])])
            itm.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            itm.setCheckState(0, Qt.Checked)

        for column in range(self.treeWidget_Movies.columnCount()):
            self.treeWidget_Movies.resizeColumnToContents(column)

        self.treeWidget_Movies.setIndentation(0)

        QApplication.instance().beep()

            # print (movie)
            #
            # break

    def onButton_Movies_Refresh(self):
        """Refresh the movies listed in self.treeWidget_Movies.

        Note: Kodi 'refreshes' a movie by deleting it and re-adding it."""

        if (self.treeWidget_Movies.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'Movie List Is Empty',
                'The movie list is empty.  Please "List" the movies first.')
            return

        response = QMessageBox.question(QApplication.instance().mainWindow, 'Are You Sure?',
            'Are you sure you want to refresh the movies for "{}"?'.format(self.comboBox_SelectDevice.currentText()))
        if (response != QMessageBox.Yes):
            return

        with QWaitCursor():
            for index in range(self.treeWidget_Movies.topLevelItemCount()):
                itm = self.treeWidget_Movies.topLevelItem(index)
                self.treeWidget_Movies.setCurrentItem(itm)
                self.treeWidget_Movies.repaint()

                if (itm.checkState(0) != Qt.Checked):
                    continue

                response = self.kodiJson.VideoLibraryRefreshMovie(int(itm.data(0, Qt.DisplayRole)))

        self.treeWidget_Movies.setCurrentItem(self.treeWidget_Movies.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_Movies_SelectAll(self):
        """Select all of the movies listed in self.treeWidget_Movies."""

        if (self.treeWidget_Movies.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'Movie List Is Empty',
                'The movie list is empty.  Please "List" the movies first.')
            return

        with QWaitCursor():
            for index in range(self.treeWidget_Movies.topLevelItemCount()):
                self.treeWidget_Movies.topLevelItem(index).setCheckState(0, Qt.Checked)

        self.treeWidget_Movies.scrollToItem(self.treeWidget_Movies.topLevelItem(0))

        QApplication.instance().beep()

    def onButton_Movies_SelectNone(self):
        """Un-select all of the movies listed in self.treeWidget_Movies."""

        if (self.treeWidget_Movies.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'Movie List Is Empty',
                'The movie list is empty.  Please "List" the movies first.')
            return

        with QWaitCursor():
            for index in range(self.treeWidget_Movies.topLevelItemCount()):
                self.treeWidget_Movies.topLevelItem(index).setCheckState(0, Qt.Unchecked)

        self.treeWidget_Movies.scrollToItem(self.treeWidget_Movies.topLevelItem(0))

        QApplication.instance().beep()

    def NewMachine(self, indexValue):
        """Update the IP Address field using the currently selected device"""

        key = self.comboBox_SelectDevice.itemData(indexValue)
        localMachine = self.localMachines.GetLocalMachine(key)

        self.label_IpAddress.setText(localMachine.ipAddress)

        self.kodiJson = KodiJson(localMachine.ipAddress, localMachine.port,
            localMachine.userId, localMachine.password, localMachine.description)

    def onButton_SelectedDevice_Ping(self):
        """Send a ping command to the selected device and display the response."""

        with QWaitCursor():
            response = self.kodiJson.ping()
        QApplication.instance().beep()

        QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))

    def onButton_SelectedDevice_Reboot(self):
        """Send a ping command to the selected device and display the response."""

        response = QMessageBox.question(QApplication.instance().mainWindow, 'Are You Sure?',
            'Are you sure you want to reboot "{}"?'.format(self.comboBox_SelectDevice.currentText()))
        if (response != QMessageBox.Yes):
            return

        with QWaitCursor():
            response = self.kodiJson.onButton_SelectedDevice_Reboot()
        QApplication.instance().beep()

        QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))

    def onButton_SelectedDevice_Version(self):
        """Get the Kodi version and the JSONRPC version."""

        waitCursor = QWaitCursor()

        kodiVersion = self.kodiJson.ApplicationVersion()
        if (type(kodiVersion) is str):
            del waitCursor
            QApplication.instance().beep()
            QMessageBox.information(QApplication.instance().mainWindow, 'Response', kodiVersion)
            return

        jsonrpcVersion = self.kodiJson.JSONRPCVersion()
        if (type(jsonrpcVersion) is str):
            del waitCursor
            QApplication.instance().beep()
            QMessageBox.information(QApplication.instance().mainWindow, 'Response', jsonrpcVersion)
            return

        del waitCursor
        QApplication.instance().beep()

        QMessageBox.information(QApplication.instance().mainWindow, 'Version Information',
            'Kodi Version: {}.{}.{} ({})\nJSONRPC Version: {}.{}.{}'.format(
            kodiVersion['major'], kodiVersion['minor'], kodiVersion['revision'], kodiVersion['tag'],
            jsonrpcVersion['major'], jsonrpcVersion['minor'], jsonrpcVersion['patch']))

    def onButton_SelectedDevice_VideoClean(self):
        """Send a command to the selected device to clean up the video library (remove missing items)."""

        with QWaitCursor():
            response = self.kodiJson.VideoLibraryClean()
        QApplication.instance().beep()

        if (response == u'OK'):
            self.statusBar.showMessage('Clean complete.', 15000)
        else:
            QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))

    def onButton_SelectedDevice_VideoUpdate(self):
        """Send a command to the selected device to update the video library (look for new items)."""

        with QWaitCursor():
            self.kodiJson.WakeUp(10.0)
            response = self.kodiJson.VideoLibraryScan()

            QApplication.instance().beep()

            if (response != u'OK'):
                QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))
                return

            self.statusBar.showMessage('Update in progress...')
            time.sleep(1.0)

            response = self.kodiJson.GetInfoBooleans('Library.IsScanningVideo')
            if (type(response) is not dict):
                QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))
                self.statusBar.showMessage('')
                return

            while (response['Library.IsScanningVideo']):
                time.sleep(1.0)

                response = self.kodiJson.GetInfoBooleans('Library.IsScanningVideo')
                if (type(response) is not dict):
                    QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))
                    self.statusBar.showMessage('')
                    return

            self.statusBar.showMessage('Update complete!', 30000)

    def SetBatchUpdateStatus(self, itm, status):
        """Set the status column for the provided item and repaint treeWidget."""

        itm.setData(2, Qt.DisplayRole, status)
        self.treeWidget_BatchUpdate.repaint()

    def onButton_TV_List(self):
        """Get a list of the TV shows on the selecte machine and display them."""

        waitCursor = QWaitCursor()
        self.treeWidget_TVShows.clear()
        response = self.kodiJson.VideoLibraryGetTVShows()

        if (type(response) is str):
            del waitCursor
            QApplication.instance().beep()
            QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))
            return

        self.statusBar.showMessage('{} TV shows found.'.format(len(response)), 15000)

        for tvShow in response:
            itm = QTreeWidgetItem(self.treeWidget_TVShows, [str(tvShow['tvshowid']), tvShow['label'], str(tvShow['year'])])
            itm.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            itm.setCheckState(0, Qt.Checked)

            seasons = self.kodiJson.VideoLibraryGetSeasons(tvShow['tvshowid'])

            if (type(response) is str):
                del waitCursor
                QApplication.instance().beep()
                QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))
                return

            for season in seasons:
                seasonItm = QTreeWidgetItem(itm, [str(season['seasonid']), season['label'], ''])

                episodes = self.kodiJson.VideoLibraryGetEpisodes(tvShow['tvshowid'], season['season'])

                if (type(response) is str):
                    del waitCursor
                    QApplication.instance().beep()
                    QMessageBox.information(QApplication.instance().mainWindow, 'Response', '"{}"'.format(response))
                    return

                for episode in episodes:
                    episodeItm = QTreeWidgetItem(seasonItm, [str(episode['episodeid']), episode['label'], ''])

        for column in range(self.treeWidget_TVShows.columnCount()):
            self.treeWidget_TVShows.resizeColumnToContents(column)

        QApplication.instance().beep()

    def onButton_TV_Refresh(self):
        """Refresh the TV shows listed in self.treeWidget_TVShows.

        Note: Kodi 'refreshes' a TV show by deleting it and re-adding it."""

        if (self.treeWidget_TVShows.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'TV Show List Is Empty',
                'The TV show list is empty.  Please "List" the TV shows first.')
            return

        response = QMessageBox.question(QApplication.instance().mainWindow, 'Are You Sure?',
            'Are you sure you want to refresh the TV shows for "{}"?'.format(self.comboBox_SelectDevice.currentText()))
        if (response != QMessageBox.Yes):
            return

        with QWaitCursor():
            for index in range(self.treeWidget_TVShows.topLevelItemCount()):
                itm = self.treeWidget_TVShows.topLevelItem(index)
                self.treeWidget_TVShows.setCurrentItem(itm)
                self.treeWidget_TVShows.repaint()

                if (itm.checkState(0) != Qt.Checked):
                    continue

                response = self.kodiJson.VideoLibraryRefreshTVShow(int(itm.data(0, Qt.DisplayRole)))

        self.treeWidget_TVShows.setCurrentItem(self.treeWidget_TVShows.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_TV_RefreshAll(self):
        """Refresh the TV shows (with episodes) listed in self.treeWidget_TVShows.

        Note: Kodi 'refreshes' a TV show by deleting it and re-adding it."""

        if (self.treeWidget_TVShows.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'TV Show List Is Empty',
                'The TV show list is empty.  Please "List" the TV shows first.')
            return

        response = QMessageBox.question(QApplication.instance().mainWindow, 'Are You Sure?',
            'Are you sure you want to refresh the TV shows and all the episodes for "{}"?'.format(self.comboBox_SelectDevice.currentText()))
        if (response != QMessageBox.Yes):
            return

        with QWaitCursor():
            for index in range(self.treeWidget_TVShows.topLevelItemCount()):
                itm = self.treeWidget_TVShows.topLevelItem(index)
                self.treeWidget_TVShows.setCurrentItem(itm)
                self.treeWidget_TVShows.repaint()

                if (itm.checkState(0) != Qt.Checked):
                    continue

                response = self.kodiJson.VideoLibraryRefreshTVShow(int(itm.data(0, Qt.DisplayRole)), refreshepisodes = True)

        self.treeWidget_TVShows.setCurrentItem(self.treeWidget_TVShows.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_TV_SelectAll(self):
        """Select all of the TV shows listed in self.treeWidget_TVShows."""

        if (self.treeWidget_TVShows.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'TV Show List Is Empty',
                'The TV show list is empty.  Please "List" the TV shows first.')
            return

        with QWaitCursor():
            for index in range(self.treeWidget_TVShows.topLevelItemCount()):
                self.treeWidget_TVShows.topLevelItem(index).setCheckState(0, Qt.Checked)

        self.treeWidget_TVShows.scrollToItem(self.treeWidget_TVShows.topLevelItem(0))

        QApplication.instance().beep()

    def onButton_TV_SelectNone(self):
        """Un-select all of the TV shows listed in self.treeWidget_TVShows."""

        if (self.treeWidget_TVShows.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow, 'TV Show List Is Empty',
                'The TV show list is empty.  Please "List" the TV shows first.')
            return

        with QWaitCursor():
            for index in range(self.treeWidget_TVShows.topLevelItemCount()):
                self.treeWidget_TVShows.topLevelItem(index).setCheckState(0, Qt.Unchecked)

        self.treeWidget_TVShows.scrollToItem(self.treeWidget_TVShows.topLevelItem(0))

        QApplication.instance().beep()

def main():
    app = MyApplication(sys.argv)
    app.mainWindow = MyMainWindow()
    app.mainWindow.show()
    app.exec_()

if (__name__ == '__main__'):
    main()
