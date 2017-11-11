#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import sys
import time

sys.path.insert(0, '/home/dave/QtProjects/Helpers')

from PyHelpers import LogTimestamp, TimedeltaToString, ElapsedTime

from PyQt5 import QtGui, QtCore
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QTreeWidgetItem

import mainwindowui
from LocalMachines import LocalMachines
from KodiJson import KodiJson
from PyQt5OverrideCursor import QWaitCursor

from Exceptions import KodiJsonResponseError

class MyApplication(QApplication):
    def __init__(self, arguments):
        super().__init__(arguments)

        self.mainWindow = None

        self.setApplicationName('KodiControl')

class MyMainWindow(QMainWindow, mainwindowui.Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.oneMinute = datetime.timedelta(minutes=1)

        self.actionQuit.triggered.connect(QApplication.instance().quit)

        self.localMachines = LocalMachines()
        self.kodiJson = None

        self.LoadLocalMachines()
        self.NewMachine(0)

        self.comboBox_SelectDevice.currentIndexChanged.connect(self.NewMachine)
        self.pushButton_Batch_AudioClean.clicked.connect(self.onButton_Batch_AudioClean)
        self.pushButton_Batch_AudioUpdate.clicked.connect(self.onButton_Batch_AudioUpdate)
        self.pushButton_Batch_ClearStatus.clicked.connect(self.onButton_Batch_ClearStatus)
        self.pushButton_Batch_PingVersion.clicked.connect(self.onButton_Batch_PingVersion)
        self.pushButton_Batch_ScanStatus.clicked.connect(self.onButton_Batch_ScanStatus)
        self.pushButton_Batch_SelectActive.clicked.connect(self.onButton_Batch_SelectActive)
        self.pushButton_Batch_SelectAll.clicked.connect(self.onButton_Batch_SelectAll)
        self.pushButton_Batch_SelectNone.clicked.connect(self.onButton_Batch_SelectNone)
        self.pushButton_Batch_VideoClean.clicked.connect(self.onButton_Batch_VideoClean)
        self.pushButton_Batch_VideoUpdate.clicked.connect(self.onButton_Batch_VideoUpdate)
        self.pushButton_Log_Clear.clicked.connect(self.onButton_Log_Clear)
        self.pushButton_Movies_List.clicked.connect(self.onButton_Movies_List)
        self.pushButton_Movies_Refresh.clicked.connect(self.onButton_Movies_Refresh)
        self.pushButton_Movies_SelectAll.clicked.connect(self.onButton_Movies_SelectAll)
        self.pushButton_Movies_SelectNone.clicked.connect(self.onButton_Movies_SelectNone)
        self.pushButton_SelectedDevice_AudioClean.clicked.connect(self.onButton_SelectedDevice_AudioClean)
        self.pushButton_SelectedDevice_AudioUpdate.clicked.connect(self.onButton_SelectedDevice_AudioUpdate)
        self.pushButton_SelectedDevice_Ping.clicked.connect(self.onButton_SelectedDevice_Ping)
        self.pushButton_SelectedDevice_Reboot.clicked.connect(self.onButton_SelectedDevice_Reboot)
        self.pushButton_SelectedDevice_ScanStatus.clicked.connect(self.onButton_SelectedDevice_ScanStatus)
        self.pushButton_SelectedDevice_Version.clicked.connect(self.onButton_SelectedDevice_Version)
        self.pushButton_SelectedDevice_VideoClean.clicked.connect(self.onButton_SelectedDevice_VideoClean)
        self.pushButton_SelectedDevice_VideoUpdate.clicked.connect(self.onButton_SelectedDevice_VideoUpdate)
        self.pushButton_SelectedDevice_WakeUp.clicked.connect(self.onButton_SelectedDevice_WakeUp)
        self.pushButton_TV_List.clicked.connect(self.onButton_TV_List)
        self.pushButton_TV_Refresh.clicked.connect(self.onButton_TV_Refresh)
        self.pushButton_TV_RefreshAll.clicked.connect(self.onButton_TV_RefreshAll)
        self.pushButton_TV_SelectAll.clicked.connect(self.onButton_TV_SelectAll)
        self.pushButton_TV_SelectNone.clicked.connect(self.onButton_TV_SelectNone)

    def batchDevice(self, kj):
        """ Returns the standard selected device string.

            Example: Batch Device: Dave's PC (192.168.4.1:8080):
        """
        return 'Batch Device: {}:'.format(kj.device)

    def formatVersion(self, kodiVersion, jsonrpcVersion, splitter='\n'):
        """ Returns a formatted string using the kodiVersion and the jsonrpcVersion.
        """
        return 'Kodi Version: {}.{}.{} ({}){}JSONRPC Version: {}.{}.{}'.format(
            kodiVersion['major'], kodiVersion['minor'],
            kodiVersion['revision'], kodiVersion['tag'],
            splitter,
            jsonrpcVersion['major'], jsonrpcVersion['minor'],
            jsonrpcVersion['patch'])

    def selectedDevice(self):
        """ Returns the standard selected device string.

            Example: Selected Device: Dave's PC (192.168.4.1:8080):
        """
        return 'Selected Device: {}:'.format(self.kodiJson.device)

    def BatchDevice_AppendStatus(self, itm, status):
        """ Appends the status to the status column for the provided item and
            repaint the treeWidget.
        """

        s = itm.data(2, Qt.DisplayRole)
        itm.setData(2, Qt.DisplayRole, s + status)
        self.treeWidget_BatchDevices.repaint()

    def BatchDevice_Ping(self, itm, kj):
        """ 'nuff said.  Returns True if the pin succeeds.
        """
        self.BatchDevice_SetStatus(itm, 'Pinging {}...'.format(kj.address))

        response = kj.ping()
        self.BatchDevice_AppendStatus(itm, response)
        self.Log_Add('Batch device ping {}: {}'.format(kj.device, response))

        if (response != 'pong'):
            return False
        return True

    def BatchDevice_ResponseError(self, itm, kj, msg, err):
        """ Show and log a response error for a batch device.
        """
        QApplication.instance().beep()
        self.BatchDevice_SetStatus(itm, '{}: {}: {}'.format(kj.address, msg, str(err)))
        self.statusBar.clearMessage()
        self.Log_Add('{} Response error: {}: {}'.format(kj.device, msg, str(err)))

    def BatchDevice_SetStatus(self, itm, status):
        """ Set the status column for the provided item and repaint the treeWidget.
        """
        itm.setData(2, Qt.DisplayRole, status)
        self.treeWidget_BatchDevices.repaint()

    def BatchDevice_WaitForMusicScan_Start(self, itm, kj):
        """ Wait for a music scan to start.
        """
        try:
            elapsedTime = ElapsedTime(self.oneMinute)

            self.Log_Add('{} Music scan: Wait for start: Start'.format(self.batchDevice(kj)))

            while (not self.IsScanningMusic(kj)):
                time.sleep(1.0)

                self.BatchDevice_SetStatus(itm,
                    '{}: Waiting for music scan to start: Elapsed time {}...'.format(
                    kj.address, str(elapsedTime)))

                if (elapsedTime.expired):
                    raise RuntimeError('Music scan: Wait for start: Timed out.')

            self.BatchDevice_SetStatus(itm,
                '{}: Music scan started: Elapsed time {}'.format(
                kj.address, str(elapsedTime)))

            self.Log_Add('{} Music scan: Wait for start: Stop'.format(self.batchDevice(kj)))

        except KodiJsonResponseError as err:
            self.BatchDevice_ResponseError(itm, kj, 'Music scan: Wait for start', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.BatchDevice_ResponseError(itm, kj, 'Music scan: Wait for start', err)

    def BatchDevice_WaitForMusicScan_Stop(self, itm, kj):
        """ Wait for a music scan to complete.
        """
        try:
            elapsedTime = ElapsedTime()

            self.Log_Add('{} Music scan: Wait for stop: Start'.format(self.batchDevice(kj)))

            while (self.IsScanningMusic(kj)):
                time.sleep(1.0)

                self.BatchDevice_SetStatus(itm,
                    '{}: Music scan in progress: Elapsed time {}...'.format(
                    kj.address, str(elapsedTime)))

                if (elapsedTime.expired):
                    raise RuntimeError('Music scan: Wait for stop: Timed out.')

            self.BatchDevice_SetStatus(itm,
                '{}: Music scan complete: Elapsed time {}'.format(
                kj.address, str(elapsedTime)))

            self.Log_Add('{} Music scan: Wait for stop: Stop'.format(self.batchDevice(kj)))

        except KodiJsonResponseError as err:
            self.BatchDevice_ResponseError(itm, kj, 'Music scan: Wait for stop', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.BatchDevice_ResponseError(itm, kj, 'Music scan: Wait for stop', err)

    def BatchDevice_WaitForVideoScan_Start(self, itm, kj):
        """ Wait for a video scan to start.
        """
        try:
            elapsedTime = ElapsedTime(self.oneMinute)

            self.Log_Add('{} Video scan: Wait for start: Start'.format(self.batchDevice(kj)))

            while (not self.IsScanningVideo(kj)):
                time.sleep(1.0)

                self.BatchDevice_SetStatus(itm,
                    '{}: Waiting for video scan to start: Elapsed time {}...'.format(
                    kj.address, str(elapsedTime)))

                if (elapsedTime.expired):
                    raise RuntimeError('Video scan: Wait for start: Timed out.')

            self.BatchDevice_SetStatus(itm,
                '{}: Video scan started: Elapsed time {}'.format(
                kj.address, str(elapsedTime)))

            self.Log_Add('{} Video scan: Wait for start: Stop'.format(self.batchDevice(kj)))

        except KodiJsonResponseError as err:
            self.BatchDevice_ResponseError(itm, kj, 'Video scan: Wait for start', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.BatchDevice_ResponseError(itm, kj, 'Video scan: Wait for start', err)

    def BatchDevice_WaitForVideoScan_Stop(self, itm, kj):
        """ Wait for a video scan to complete.
        """
        try:
            elapsedTime = ElapsedTime()

            self.Log_Add('{} Video scan: Wait for stop: Start'.format(self.batchDevice(kj)))

            while (self.IsScanningVideo(kj)):
                time.sleep(1.0)

                self.BatchDevice_SetStatus(itm,
                    '{}: Video scan in progress: Elapsed time {}...'.format(
                    kj.address, str(elapsedTime)))

                if (elapsedTime.expired):
                    raise RuntimeError('Video scan: Wait for stop: Timed out.')

            self.BatchDevice_SetStatus(itm,
                '{}: Video scan complete: Elapsed time {}'.format(
                kj.address, str(elapsedTime)))

            self.Log_Add('{} Video scan: Wait for stop: Stop'.format(self.batchDevice(kj)))

        except KodiJsonResponseError as err:
            self.BatchDevice_ResponseError(itm, kj, 'Video scan: Wait for stop', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.BatchDevice_ResponseError(itm, kj, 'Video scan: Wait for stop', err)

    def BatchDevices_ClearStatus(self):
        """ Clear the 'status' column in self.treeWidget_BatchDevices.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):
                itm = self.treeWidget_BatchDevices.topLevelItem(index)
                self.treeWidget_BatchDevices.scrollToItem(itm)
                itm.setData(2, Qt.DisplayRole, '')

        self.treeWidget_BatchDevices.scrollToItem(self.treeWidget_BatchDevices.topLevelItem(0))

    def BatchDevices_TreeIsEmpty(self):
        """ Make sure the batch devices list is not empty.
        """
        if (self.treeWidget_BatchDevices.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow,
                'Batch Devices List Is Empty',
                'The batch devices list is empty.  Unable to continue.')
            return True

        return False

    def BatchUpdate_GetCheckedItem(self, index):
        """ Returns the indexed, checked item from the batch update tree.
            Visably selects each item.
            Adds a half-second delay if the item is not checked.
        """
        itm = self.treeWidget_BatchDevices.topLevelItem(index)
        self.treeWidget_BatchDevices.setCurrentItem(itm)
        self.treeWidget_BatchDevices.repaint()

        if (itm.checkState(1) != Qt.Checked):
            time.sleep(0.5)
            return None

        return itm

    def BatchUpdate_GetKodiJson(self, itm):
        """ Returns a tuple of the local machine object and a KodiJson object
            for the passed item.
        """
        key = int(itm.data(0, Qt.DisplayRole))
        lm = self.localMachines.LOCAL_MACHINES[key]
        kj = KodiJson(lm.ipAddress, lm.port, lm.userId, lm.password, lm.description)

        return (lm, kj)

    def IsScanning(self, kj):
        """ See if the target machine is scanning for new music or new videos.
            An exception is raised if an invalid response occurs.
        """
        response = kj.GetInfoBooleans(['Library.IsScanningMusic', 'Library.IsScanningVideo'])
        return (response['Library.IsScanningMusic'] | response['Library.IsScanningVideo'])

    def IsScanningMusic(self, kj):
        """ See if the target machine is scanning for new music.
            An exception is raised if an invalid response occurs.
        """
        response = kj.GetInfoBooleans('Library.IsScanningMusic')
        return (response['Library.IsScanningMusic'])

    def IsScanningVideo(self, kj):
        """ See if the target machine is scanning for new videos.
            An exception is raised if an invalid response occurs.
        """
        response = kj.GetInfoBooleans('Library.IsScanningVideo')
        return (response['Library.IsScanningVideo'])

    def LoadLocalMachines(self):
        """ Load the local machines into the combo box.
        """
        data = []

        for key in self.localMachines.LOCAL_MACHINES.keys():
            lm = self.localMachines.LOCAL_MACHINES[key]
            data.append((lm.description, lm.active, key))

        data.sort()
        for (description, active, key) in data:
            self.comboBox_SelectDevice.addItem(description, key)

            itm = QTreeWidgetItem(self.treeWidget_BatchDevices, [str(key), description, ''])
            itm.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            if (active):
                itm.setCheckState(1, Qt.Checked)
            else:
                itm.setCheckState(1, Qt.Unchecked)

        self.treeWidget_BatchDevices.setColumnHidden(0, True)
        self.treeWidget_BatchDevices.resizeColumnToContents(1)
        self.treeWidget_BatchDevices.setColumnWidth(1, self.treeWidget_BatchDevices.columnWidth(1) + 20)

    def Log_Add(self, lineOfText):
        """ Add a line to the log.
        """
        self.listWidget_Log.addItem('{} {}'.format(LogTimestamp(), lineOfText))

    def MovieListIsEmpty(self):
        """ Make sure the movie list is not empty.
        """
        if (self.treeWidget_Movies.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow,
                'Movie List Is Empty',
                'The movie list is empty.  Please "List" the movies first.')
            return True

        return False

    def NewMachine(self, indexValue):
        """ Update the IP Address field using the currently selected device.
        """
        key = self.comboBox_SelectDevice.itemData(indexValue)
        localMachine = self.localMachines.GetLocalMachine(key)

        self.label_IpAddress.setText(localMachine.ipAddress)

        self.kodiJson = KodiJson(localMachine.ipAddress, localMachine.port,
            localMachine.userId, localMachine.password, localMachine.description)

    def TVListIsEmpty(self):
        """ Make sure the TV list is not empty.
        """
        if (self.treeWidget_TVShows.topLevelItemCount() == 0):
            QMessageBox.warning(QApplication.instance().mainWindow,
                'TV List Is Empty',
                'The TV list is empty.  Please "List" the TV shows first.')
            return True

        return False

    def onButton_Batch_AudioClean(self):
        """ In sequence, send a command to each batch device to clean the
            audio library (remove deleted items).  Wait for each device to
            complete (or time out) before starting the next device.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        self.Log_Add('Batch audio clean: Start')
        self.BatchDevices_ClearStatus()

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):
                itm = self.BatchUpdate_GetCheckedItem(index)
                if (itm is None):
                    continue
                lm, kj = self.BatchUpdate_GetKodiJson(itm)

                try:
                    if (not self.BatchDevice_Ping(itm, kj)):
                        continue

                    kj.WakeUp(10.0)

                    if (self.IsScanningVideo(kj)):
                        self.BatchDevice_WaitForVideoScan_Stop(itm, kj)

                    if (self.IsScanningMusic(kj)):
                        self.BatchDevice_WaitForMusicScan_Stop(itm, kj)

                    self.BatchDevice_SetStatus(itm,
                        '{}: Music clean started...'.format(kj.address))
                    self.Log_Add('{} Music clean: Start'.format(self.batchDevice(kj)))
                    kj.AudioLibrary_Clean()
                    self.Log_Add('{} Music clean: Stop'.format(self.batchDevice(kj)))
                    self.BatchDevice_AppendStatus(itm, 'Clean complete!')

                except KodiJsonResponseError as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Audio update', err)
                except (ConnectionResetError, RuntimeError) as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Audio update', err)

        self.treeWidget_BatchDevices.setCurrentItem(self.treeWidget_BatchDevices.topLevelItem(0))
        self.Log_Add('Batch audio clean: Stop')
        QApplication.instance().beep()

    def onButton_Batch_AudioUpdate(self):
        """ In sequence, send a command to each batch device to update the
            audio library (look for new items).  Wait for each device to
            complete (or time out) before starting the next device.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        self.Log_Add('Batch audio update: Start')
        self.BatchDevices_ClearStatus()

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):
                itm = self.BatchUpdate_GetCheckedItem(index)
                if (itm is None):
                    continue
                lm, kj = self.BatchUpdate_GetKodiJson(itm)

                try:
                    if (not self.BatchDevice_Ping(itm, kj)):
                        continue

                    kj.WakeUp(10.0)

                    if (self.IsScanningVideo(kj)):
                        self.BatchDevice_WaitForVideoScan_Stop(itm, kj)

                    if (self.IsScanningMusic(kj)):
                        self.BatchDevice_WaitForMusicScan_Stop(itm, kj)
                    else:
                        kj.AudioLibrary_Scan()
                        self.BatchDevice_WaitForMusicScan_Start(itm, kj)
                        self.BatchDevice_WaitForMusicScan_Stop(itm, kj)

                    # self.BatchDevice_AppendStatus(itm, 'Scan complete!')

                    if (self.checkBox_Batch_CleanAfterUpdate.isChecked()):
                        self.BatchDevice_AppendStatus(itm, '; Clean started...')
                        self.Log_Add('{} Audio clean: Start'.format(self.batchDevice(kj)))
                        kj.AudioLibrary_Clean()
                        self.Log_Add('{} Audio clean: Stop'.format(self.batchDevice(kj)))
                        self.BatchDevice_AppendStatus(itm, 'Clean complete!')

                except KodiJsonResponseError as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Audio update', err)
                except (ConnectionResetError, RuntimeError) as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Audio update', err)

        self.treeWidget_BatchDevices.setCurrentItem(self.treeWidget_BatchDevices.topLevelItem(0))
        self.Log_Add('Batch audio update: Stop')
        QApplication.instance().beep()

    def onButton_Batch_ClearStatus(self):
        """ Clear the 'status' column in self.treeWidget_BatchDevices.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        self.BatchDevices_ClearStatus()
        QApplication.instance().beep()

    def onButton_Batch_PingVersion(self):
        """ Ping each batch device and retrieve it's Kodi version and it's
            Koci JSON version.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        self.Log_Add('Batch ping & version: Start')
        self.BatchDevices_ClearStatus()

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):
                itm = self.BatchUpdate_GetCheckedItem(index)
                if (itm is None):
                    continue
                lm, kj = self.BatchUpdate_GetKodiJson(itm)

                try:
                    if (not self.BatchDevice_Ping(itm, kj)):
                        continue

                    kodiVersion = kj.GetApplicationVersion()
                    jsonrpcVersion = kj.GetJSONRPCVersion()

                except KodiJsonResponseError as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Batch ping & version', err)
                    continue
                except (ConnectionResetError, RuntimeError) as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Batch ping & version', err)
                    continue

                s = self.formatVersion(kj.GetApplicationVersion(), kj.GetJSONRPCVersion())
                self.BatchDevice_SetStatus(itm, '{}: {}'.format(kj.address, s))
                self.Log_Add('Batch device: {}: {}'.format(kj.device, s))

            self.treeWidget_BatchDevices.setCurrentItem(self.treeWidget_BatchDevices.topLevelItem(0))

        self.Log_Add('Batch ping & version: Stop')
        QApplication.instance().beep()

    def onButton_Batch_ScanStatus(self):
        """ Determine if a music library scan or a video library scan is
            running for each batch device.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        self.Log_Add('Batch scan status: Start')
        self.BatchDevices_ClearStatus()

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):
                itm = self.BatchUpdate_GetCheckedItem(index)
                if (itm is None):
                    continue
                lm, kj = self.BatchUpdate_GetKodiJson(itm)

                try:
                    musicScan = self.IsScanningMusic(kj)
                    videoScan = self.IsScanningVideo(kj)

                except KodiJsonResponseError as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Batch scan status', err)
                    continue
                except (ConnectionResetError, RuntimeError) as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Batch scan status', err)
                    continue

                s = 'Scan Status: Music scan: {}; Video scan: {}'.format(
                    musicScan, videoScan)
                self.BatchDevice_SetStatus(itm, '{}: {}'.format(kj.address, s))
                self.Log_Add('Batch device: {}: {}'.format(kj.device, s))

            self.treeWidget_BatchDevices.setCurrentItem(self.treeWidget_BatchDevices.topLevelItem(0))

        self.Log_Add('Batch scan status: Stop')
        QApplication.instance().beep()

    def onButton_Batch_SelectActive(self):
        """ Select all of the 'active' devices listed in self.treeWidget_BatchDevices.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):

                itm = self.treeWidget_BatchDevices.topLevelItem(index)
                key = int(itm.data(0, Qt.DisplayRole))
                lm = self.localMachines.LOCAL_MACHINES[key]

                if (lm.active):
                    itm.setCheckState(1, Qt.Checked)
                else:
                    itm.setCheckState(1, Qt.Unchecked)

        self.treeWidget_BatchDevices.scrollToItem(self.treeWidget_BatchDevices.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_Batch_SelectAll(self):
        """ Select all of the devices listed in self.treeWidget_BatchDevices.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):
                itm = self.treeWidget_BatchDevices.topLevelItem(index)
                self.treeWidget_BatchDevices.scrollToItem(itm)
                itm.setCheckState(1, Qt.Checked)

        self.treeWidget_BatchDevices.scrollToItem(self.treeWidget_BatchDevices.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_Batch_SelectNone(self):
        """ Un-select all of the devices listed in self.treeWidget_BatchDevices.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):
                itm = self.treeWidget_BatchDevices.topLevelItem(index)
                self.treeWidget_BatchDevices.scrollToItem(itm)
                itm.setCheckState(1, Qt.Unchecked)

        self.treeWidget_BatchDevices.scrollToItem(self.treeWidget_BatchDevices.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_Batch_VideoClean(self):
        """ In sequence, send a command to each batch device to clean the
            video library (remove deleted items).  Wait for each device to
            complete (or time out) before starting the next device.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        self.Log_Add('Batch video clean: Start')
        self.BatchDevices_ClearStatus()

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):
                itm = self.BatchUpdate_GetCheckedItem(index)
                if (itm is None):
                    continue
                lm, kj = self.BatchUpdate_GetKodiJson(itm)

                try:
                    if (not self.BatchDevice_Ping(itm, kj)):
                        continue

                    kj.WakeUp(10.0)

                    if (self.IsScanningVideo(kj)):
                        self.BatchDevice_WaitForVideoScan_Stop(itm, kj)

                    if (self.IsScanningMusic(kj)):
                        self.BatchDevice_WaitForMusicScan_Stop(itm, kj)

                    self.BatchDevice_SetStatus(itm,
                        '{}: Video clean started...'.format(kj.address))
                    self.Log_Add('{} Video clean: Start'.format(self.batchDevice(kj)))
                    kj.VideoLibrary_Clean()
                    self.Log_Add('{} Video clean: Stop'.format(self.batchDevice(kj)))
                    self.BatchDevice_AppendStatus(itm, 'Clean complete!')

                except KodiJsonResponseError as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Video update', err)
                except (ConnectionResetError, RuntimeError) as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Video update', err)

        self.treeWidget_BatchDevices.setCurrentItem(self.treeWidget_BatchDevices.topLevelItem(0))
        self.Log_Add('Batch video clean: Stop')
        QApplication.instance().beep()

    def onButton_Batch_VideoUpdate(self):
        """ In sequence, send a command to each batch device to update the
            video library (look for new items).  Wait for each device to
            complete (or time out) before starting the next device.
        """
        if self.BatchDevices_TreeIsEmpty():
            return

        self.Log_Add('Batch video update: Start')
        self.BatchDevices_ClearStatus()

        with QWaitCursor():
            for index in range(self.treeWidget_BatchDevices.topLevelItemCount()):
                itm = self.BatchUpdate_GetCheckedItem(index)
                if (itm is None):
                    continue
                lm, kj = self.BatchUpdate_GetKodiJson(itm)

                try:
                    if (not self.BatchDevice_Ping(itm, kj)):
                        continue

                    kj.WakeUp(10.0)

                    if (self.IsScanningMusic(kj)):
                        self.BatchDevice_WaitForMusicScan_Stop(itm, kj)

                    if (self.IsScanningVideo(kj)):
                        self.BatchDevice_WaitForVideoScan_Stop(itm, kj)
                    else:
                        kj.VideoLibrary_Scan()
                        self.BatchDevice_WaitForVideoScan_Start(itm, kj)
                        self.BatchDevice_WaitForVideoScan_Stop(itm, kj)

                    # self.BatchDevice_AppendStatus(itm, 'Scan complete!')

                    if (self.checkBox_Batch_CleanAfterUpdate.isChecked()):
                        self.BatchDevice_AppendStatus(itm, '; Clean started...')
                        self.Log_Add('{} Video clean: Start'.format(self.batchDevice(kj)))
                        kj.VideoLibrary_Clean()
                        self.Log_Add('{} Video clean: Stop'.format(self.batchDevice(kj)))
                        self.BatchDevice_AppendStatus(itm, 'Clean complete!')

                except KodiJsonResponseError as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Video update', err)
                except (ConnectionResetError, RuntimeError) as err:
                    self.BatchDevice_ResponseError(itm, kj, 'Video update', err)

        self.treeWidget_BatchDevices.setCurrentItem(self.treeWidget_BatchDevices.topLevelItem(0))
        self.Log_Add('Batch video update: Stop')
        QApplication.instance().beep()

    def onButton_Log_Clear(self):
        """ Clear the log.
        """

        self.listWidget_Log.clear()

    def onButton_Movies_List(self):
        """ Get a list of the movies on the selecte machine and display them.
        """
        try:
            with QWaitCursor():
                self.treeWidget_Movies.clear()
                self.treeWidget_Movies.resetIndentation()
                self.Log_Add('{} Movies list start'.format(self.selectedDevice()))

                response = self.kodiJson.VideoLibrary_GetMovies()
                movieCount = len(response)
                self.statusBar.showMessage('{} movies found.'.format(movieCount), 15000)

                for movie in response:
                    itm = QTreeWidgetItem(self.treeWidget_Movies, [str(movie['movieid']), movie['label'], str(movie['year'])])
                    itm.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    itm.setCheckState(0, Qt.Checked)

                for column in range(self.treeWidget_Movies.columnCount()):
                    self.treeWidget_Movies.resizeColumnToContents(column)

                self.treeWidget_Movies.setIndentation(0)
                self.Log_Add('{} Movies list stop: {} movies found'.format(
                    self.selectedDevice(), movieCount))
                QApplication.instance().beep()

        except KodiJsonResponseError as err:
            # self.statusBar.clearMessage()
            self.SelectedDevice_ResponseError('List movies', err)

    def onButton_Movies_Refresh(self):
        """ Refresh the movies listed in self.treeWidget_Movies.

            Note: Kodi 'refreshes' a movie by deleting it and re-adding it.
        """
        if self.MovieListIsEmpty():
            return

        response = QMessageBox.question(QApplication.instance().mainWindow, 'Are You Sure?',
            'Are you sure you want to refresh the movies for "{}"?'.format(self.comboBox_SelectDevice.currentText()))
        if (response != QMessageBox.Yes):
            return

        moviesRefreshed = 0
        self.Log_Add('{} Movies refresh start'.format(self.selectedDevice()))

        try:
            with QWaitCursor():
                self.kodiJson.WakeUp(10.0)
                for index in range(self.treeWidget_Movies.topLevelItemCount()):
                    itm = self.treeWidget_Movies.topLevelItem(index)
                    self.treeWidget_Movies.setCurrentItem(itm)
                    self.treeWidget_Movies.repaint()

                    if (itm.checkState(0) != Qt.Checked):
                        continue

                    response = self.kodiJson.VideoLibrary_RefreshMovie(int(itm.data(0, Qt.DisplayRole)))
                    moviesRefreshed += 1

            self.statusBar.showMessage('{} {} of {} movies refreshed.'.format(
                self.selectedDevice(), moviesRefreshed,
                self.treeWidget_Movies.topLevelItemCount()), 15000)
            self.Log_Add('{} Movies refresh stop: {} of {} movies refreshed'.format(
                self.selectedDevice(), moviesRefreshed,
                self.treeWidget_Movies.topLevelItemCount()))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Movies refresh', err)

        self.treeWidget_Movies.setCurrentItem(self.treeWidget_Movies.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_Movies_SelectAll(self):
        """ Select all of the movies listed in self.treeWidget_Movies.
        """
        if self.MovieListIsEmpty():
            return

        with QWaitCursor():
            for index in range(self.treeWidget_Movies.topLevelItemCount()):
                itm = self.treeWidget_Movies.topLevelItem(index)
                self.treeWidget_Movies.scrollToItem(itm)
                itm.setCheckState(0, Qt.Checked)

        self.treeWidget_Movies.scrollToItem(self.treeWidget_Movies.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_Movies_SelectNone(self):
        """ Un-select all of the movies listed in self.treeWidget_Movies.
        """
        if self.MovieListIsEmpty():
            return

        with QWaitCursor():
            for index in range(self.treeWidget_Movies.topLevelItemCount()):
                itm = self.treeWidget_Movies.topLevelItem(index)
                self.treeWidget_Movies.scrollToItem(itm)
                itm.setCheckState(0, Qt.Unchecked)

        self.treeWidget_Movies.scrollToItem(self.treeWidget_Movies.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_SelectedDevice_AudioClean(self):
        """ Send a command to the selected device to clean the audio library
            (remove missing items).
        """
        self.Log_Add('{} Audio clean start'.format(self.selectedDevice()))
        self.statusBar.showMessage('{} Audio clean start.'.format(self.selectedDevice()), 15000)

        try:
            with QWaitCursor():
                self.kodiJson.WakeUp(10.0)
                response = self.kodiJson.AudioLibrary_Clean()

            QApplication.instance().beep()
            self.statusBar.showMessage('{} Audio clean complete.'.format(self.selectedDevice()), 15000)
            self.Log_Add('{} Audio clean start'.format(self.selectedDevice()))

        except KodiJsonResponseError as err:
            # self.statusBar.clearMessage()
            self.SelectedDevice_ResponseError('Audio clean', err)

    def onButton_SelectedDevice_AudioUpdate(self):
        """ Send a command to the selected device to update the audio library
            (look for new items).
        """
        self.Log_Add('{} Audio update start'.format(self.selectedDevice()))
        self.statusBar.showMessage('{} Audio update start.'.format(self.selectedDevice()), 15000)

        try:
            with QWaitCursor():
                self.kodiJson.WakeUp(10.0)

                if (self.IsScanningVideo(self.kodiJson)):
                    self.SelectedDevice_WaitForVideoScan_Stop()

                if (self.IsScanningMusic(self.kodiJson)):
                    self.SelectedDevice_WaitForMusicScan_Stop()
                else:
                    self.kodiJson.AudioLibrary_Scan()
                    self.SelectedDevice_WaitForMusicScan_Start()
                    self.SelectedDevice_WaitForMusicScan_Stop()

            QApplication.instance().beep()
            self.statusBar.showMessage('{} Audio update complete.'.format(self.selectedDevice()), 15000)
            self.Log_Add('{} Audio update stop'.format(self.selectedDevice()))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Audio update', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.SelectedDevice_ResponseError('Audio update', err)

    def onButton_SelectedDevice_Ping(self):
        """ Send a ping command to the selected device and display the response.
        """
        with QWaitCursor():
            response = self.kodiJson.ping()

        QApplication.instance().beep()
        QMessageBox.information(QApplication.instance().mainWindow, 'Response',
            '{}\n{}'.format(self.selectedDevice(), response))
        self.Log_Add('{} Ping: {}'.format(self.selectedDevice(), response))

    def onButton_SelectedDevice_Reboot(self):
        """ Send a reboot command to the selected device.
        """
        response = QMessageBox.question(QApplication.instance().mainWindow, 'Are You Sure?',
            'Are you sure you want to reboot "{}"?'.format(self.comboBox_SelectDevice.currentText()))
        if (response != QMessageBox.Yes):
            return

        try:
            with QWaitCursor():
                response = self.kodiJson.Reboot()

            QApplication.instance().beep()
            QMessageBox.information(QApplication.instance().mainWindow,
                'Response', '{}\n{}'.format(self.selectedDevice(), response))
            self.Log_Add('{} Reboot: {}'.format(self.selectedDevice(), response))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Reboot', err)

    def onButton_SelectedDevice_ScanStatus(self):
        """ Determine the audio library and video library scan status of the
            selected device.
        """
        try:
            with QWaitCursor():
                musicScan = self.IsScanningMusic(self.kodiJson)
                videoScan = self.IsScanningVideo(self.kodiJson)

            QApplication.instance().beep()
            QMessageBox.information(QApplication.instance().mainWindow,
                'Scan Status', 'Music scan: {}\nVideo scan: {}'.format(
                musicScan, videoScan))
            self.Log_Add('{} Scan status: Music scan: {}; Video scan: {}'.format(
                self.selectedDevice(), musicScan, videoScan))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Scan status', err)

    def onButton_SelectedDevice_Version(self):
        """ Get the Kodi version and the JSONRPC version.
        """
        try:
            with QWaitCursor():
                kodiVersion = self.kodiJson.GetApplicationVersion()
                jsonrpcVersion = self.kodiJson.GetJSONRPCVersion()

            QApplication.instance().beep()
            QMessageBox.information(QApplication.instance().mainWindow,
                'Version Information', self.formatVersion(kodiVersion,
                jsonrpcVersion))
            self.Log_Add('{} {}'.format(self.selectedDevice(),
                self.formatVersion(kodiVersion, jsonrpcVersion, splitter=': ')))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Version', err)

    def onButton_SelectedDevice_VideoClean(self):
        """ Send a command to the selected device to clean up the video library
            (remove missing items).
        """
        self.Log_Add('{} Video clean start'.format(self.selectedDevice()))
        self.statusBar.showMessage('{} Video clean start.'.format(self.selectedDevice()), 15000)

        try:
            with QWaitCursor():
                self.kodiJson.WakeUp(10.0)
                response = self.kodiJson.VideoLibrary_Clean()

            QApplication.instance().beep()
            self.statusBar.showMessage('{} Video clean complete.'.format(self.selectedDevice()), 15000)
            self.Log_Add('{} Video clean start'.format(self.selectedDevice()))

        except KodiJsonResponseError as err:
            # self.statusBar.clearMessage()
            self.SelectedDevice_ResponseError('Video clean', err)

    def onButton_SelectedDevice_VideoUpdate(self):
        """ Send a command to the selected device to update the video library
            (look for new items).
        """
        self.Log_Add('{} Video update start'.format(self.selectedDevice()))
        self.statusBar.showMessage('{} Video update start.'.format(self.selectedDevice()), 15000)

        try:
            with QWaitCursor():
                self.kodiJson.WakeUp(10.0)

                if (self.IsScanningMusic(self.kodiJson)):
                    self.SelectedDevice_WaitForMusicScan_Stop()

                if (self.IsScanningVideo(self.kodiJson)):
                    self.SelectedDevice_WaitForVideoScan_Stop()
                else:
                    self.kodiJson.VideoLibrary_Scan()
                    self.SelectedDevice_WaitForVideoScan_Start()
                    self.SelectedDevice_WaitForVideoScan_Stop()

            QApplication.instance().beep()
            self.statusBar.showMessage('{} Video update complete.'.format(self.selectedDevice()), 15000)
            self.Log_Add('{} Video update stop'.format(self.selectedDevice()))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Video update', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.SelectedDevice_ResponseError('Video update', err)

    def onButton_SelectedDevice_WakeUp(self):
        """ Get the Kodi version and the JSONRPC version.
        """
        try:
            with QWaitCursor():
                self.kodiJson.WakeUp()
            QApplication.instance().beep()
            QMessageBox.information(QApplication.instance().mainWindow,
                'Wake Up', 'Wake up command successfully sent.')

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Wake up', err)

    def onButton_TV_List(self):
        """ Get a list of the TV shows on the selecte machine and display them.
        """
        try:
            with QWaitCursor():
                self.treeWidget_TVShows.clear()
                self.treeWidget_Movies.resetIndentation()
                self.Log_Add('{} TV shows list start'.format(self.selectedDevice()))

                response = self.kodiJson.VideoLibrary_GetTVShows()
                tvShowCount = len(response)
                self.statusBar.showMessage('{} TV shows found.'.format(tvShowCount), 15000)

                tvShowNumber = 0
                for tvShow in response:

                    tvShowNumber += 1
                    tvShowId = tvShow['tvshowid']
                    tvShowLabel = tvShow['label']
                    tvShowYear = tvShow['year']
                    self.statusBar.showMessage('TV show {} of {}: {} (ID {})'.format(
                        tvShowNumber, tvShowCount, tvShowLabel, tvShowId), 15000)

                    itm = QTreeWidgetItem(self.treeWidget_TVShows, [str(tvShowId), tvShowLabel, str(tvShowYear)])
                    itm.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    itm.setCheckState(0, Qt.Checked)

                    seasons = self.kodiJson.VideoLibrary_GetSeasons(tvShow['tvshowid'])
                    for season in seasons:
                        seasonItm = QTreeWidgetItem(itm, [str(season['seasonid']), season['label'], ''])

                        episodes = self.kodiJson.VideoLibrary_GetEpisodes(tvShow['tvshowid'], season['season'])
                        for episode in episodes:
                            episodeItm = QTreeWidgetItem(seasonItm, [str(episode['episodeid']), episode['label'], ''])

                for column in range(self.treeWidget_TVShows.columnCount()):
                    self.treeWidget_TVShows.resizeColumnToContents(column)
                self.Log_Add('{} TV shows list stop: {} TV shows found'.format(
                    self.selectedDevice(), tvShowCount))
                QApplication.instance().beep()

        except KodiJsonResponseError as err:
            # self.statusBar.clearMessage()
            self.SelectedDevice_ResponseError('List TV shows', err)

    def onButton_TV_Refresh(self):
        """ Refresh the TV shows listed in self.treeWidget_TVShows.

            Note: Kodi 'refreshes' a TV show by deleting it and re-adding it.
        """
        if (self.TVListIsEmpty()):
            return

        response = QMessageBox.question(QApplication.instance().mainWindow, 'Are You Sure?',
            'Are you sure you want to refresh the TV shows for "{}"?'.format(self.comboBox_SelectDevice.currentText()))
        if (response != QMessageBox.Yes):
            return

        tvShowsRefreshed = 0
        self.Log_Add('{} TV shows refresh start'.format(self.selectedDevice()))

        try:
            with QWaitCursor():
                for index in range(self.treeWidget_TVShows.topLevelItemCount()):
                    itm = self.treeWidget_TVShows.topLevelItem(index)
                    self.treeWidget_TVShows.setCurrentItem(itm)
                    self.treeWidget_TVShows.repaint()

                    if (itm.checkState(0) != Qt.Checked):
                        continue

                    response = self.kodiJson.VideoLibrary_RefreshTVShow(int(itm.data(0, Qt.DisplayRole)))
                    tvShowsRefreshed += 1

            self.statusBar.showMessage('{} {} of {} TV shows refreshed.'.format(
                self.selectedDevice(), tvShowsRefreshed,
                self.treeWidget_TVShows.topLevelItemCount()), 15000)
            self.Log_Add('{} TV shows refresh stop: {} of {} TV shows refreshed'.format(
                self.selectedDevice(), tvShowsRefreshed,
                self.treeWidget_TVShows.topLevelItemCount()))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('TV refresh', err)

        self.treeWidget_TVShows.setCurrentItem(self.treeWidget_TVShows.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_TV_RefreshAll(self):
        """ Refresh the TV shows (with episodes) listed in self.treeWidget_TVShows.

            Note: Kodi 'refreshes' a TV show by deleting it and re-adding it.
        """
        if (self.TVListIsEmpty()):
            return

        response = QMessageBox.question(QApplication.instance().mainWindow, 'Are You Sure?',
            'Are you sure you want to refresh the TV shows and all the episodes for "{}"?'.format(
            self.comboBox_SelectDevice.currentText()))
        if (response != QMessageBox.Yes):
            return

        tvShowsRefreshed = 0
        self.Log_Add('{} TV shows refresh all start'.format(self.selectedDevice()))

        try:
            with QWaitCursor():
                for index in range(self.treeWidget_TVShows.topLevelItemCount()):
                    itm = self.treeWidget_TVShows.topLevelItem(index)
                    self.treeWidget_TVShows.setCurrentItem(itm)
                    self.treeWidget_TVShows.repaint()

                    if (itm.checkState(0) != Qt.Checked):
                        continue

                    response = self.kodiJson.VideoLibrary_RefreshTVShow(int(itm.data(0, Qt.DisplayRole)), refreshepisodes = True)
                    tvShowsRefreshed += 1

            self.statusBar.showMessage('{} {} of {} TV shows refreshed.'.format(
                self.selectedDevice(), tvShowsRefreshed,
                self.treeWidget_TVShows.topLevelItemCount()), 15000)
            self.Log_Add('{} TV shows refresh all stop: {} of {} TV shows refreshed'.format(
                self.selectedDevice(), tvShowsRefreshed,
                self.treeWidget_TVShows.topLevelItemCount()))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('TV refresh', err)

        self.treeWidget_TVShows.setCurrentItem(self.treeWidget_TVShows.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_TV_SelectAll(self):
        """ Select all of the TV shows listed in self.treeWidget_TVShows.
        """
        if self.TVListIsEmpty():
            return

        with QWaitCursor():
            for index in range(self.treeWidget_TVShows.topLevelItemCount()):
                itm = self.treeWidget_TVShows.topLevelItem(index)
                self.treeWidget_TVShows.scrollToItem(itm)
                itm.setCheckState(0, Qt.Checked)

        self.treeWidget_TVShows.scrollToItem(self.treeWidget_TVShows.topLevelItem(0))
        QApplication.instance().beep()

    def onButton_TV_SelectNone(self):
        """ Un-select all of the TV shows listed in self.treeWidget_TVShows.
        """
        if self.TVListIsEmpty():
            return

        with QWaitCursor():
            for index in range(self.treeWidget_TVShows.topLevelItemCount()):
                itm = self.treeWidget_TVShows.topLevelItem(index)
                self.treeWidget_TVShows.scrollToItem(itm)
                itm.setCheckState(0, Qt.Unchecked)

        self.treeWidget_TVShows.scrollToItem(self.treeWidget_TVShows.topLevelItem(0))
        QApplication.instance().beep()

    def SelectedDevice_ResponseError(self, msg, err):
        """ Show and log a response error for a selected device.
        """
        QApplication.instance().beep()
        QMessageBox.information(QApplication.instance().mainWindow, 'Response Error',
            '{}\n{}'.format(self.selectedDevice(), str(err)))
        self.statusBar.clearMessage()
        self.Log_Add('{} Response error: {}: {}'.format(self.kodiJson.device, msg, str(err)))

    def SelectedDevice_WaitForMusicScan_Start(self):
        """ Wait for an audio update to start.
        """
        try:
            elapsedTime = ElapsedTime(self.oneMinute)

            self.Log_Add('{} Music scan: Wait for start: Start'.format(self.selectedDevice()))

            while (not self.IsScanningMusic(self.kodiJson)):
                time.sleep(1.0)

                self.statusBar.showMessage(
                    'Audio scan in progress: Elapsed time {}...'.format(
                    str(elapsedTime)), 15000)

                if (elapsedTime.expired):
                    raise RuntimeError('Music scan: Wait for start: Timed out.')

            self.Log_Add('{} Music scan: Wait for start: Stop'.format(self.selectedDevice()))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Music scan: Wait for start', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.SelectedDevice_ResponseError('Music scan: Wait for start', err)

    def SelectedDevice_WaitForMusicScan_Stop(self):
        """ Wait for an audio update to complete.
        """
        try:
            elapsedTime = ElapsedTime()
            # elapsedTime = ElapsedTime(datetime.timedelta(seconds=15))

            self.Log_Add('{} Music scan: Wait for stop: Start'.format(self.selectedDevice()))

            while (self.IsScanningMusic(self.kodiJson)):
                time.sleep(1.0)

                self.statusBar.showMessage('Audio scan in progress: Elapsed time {}...'.format(
                    str(elapsedTime)), 15000)

                if (elapsedTime.expired):
                    raise RuntimeError('Music scan: Wait for stop: Timed out.')

            self.Log_Add('{} Music scan: Wait for stop: Stop'.format(self.selectedDevice()))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Music scan: Wait for stop', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.SelectedDevice_ResponseError('Music scan: Wait for stop', err)

    def SelectedDevice_WaitForVideoScan_Start(self):
        """ Wait for a video scan to start.
        """
        try:
            elapsedTime = ElapsedTime(self.oneMinute)

            self.Log_Add('{} Video scan: Wait for start: Start'.format(self.selectedDevice()))

            while (not self.IsScanningVideo(self.kodiJson)):
                time.sleep(1.0)

                self.statusBar.showMessage('Waiting for video scan start: Elapsed time {}...'.format(
                    str(elapsedTime)), 15000)

                if (elapsedTime.expired):
                    raise RuntimeError('Video scan: Wait for start: Timed out.')

            self.Log_Add('{} Video scan: Wait for start: Stop'.format(self.selectedDevice()))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Video scan: Wait for start', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.SelectedDevice_ResponseError('Video scan: Wait for start', err)

    def SelectedDevice_WaitForVideoScan_Stop(self):
        """ Wait for a video scan to complete.
        """
        try:
            elapsedTime = ElapsedTime()

            self.Log_Add('{} Video scan: Wait for stop: Start'.format(self.selectedDevice()))

            while (self.IsScanningVideo(self.kodiJson)):
                time.sleep(1.0)

                self.statusBar.showMessage('Video scan in progress: Elapsed time {}...'.format(
                    str(elapsedTime)), 15000)

                if (elapsedTime.expired):
                    raise RuntimeError('Video scan: Wait for stop: Timed out.')

            self.Log_Add('{} Video scan: Wait for stop: Stop'.format(self.selectedDevice()))

        except KodiJsonResponseError as err:
            self.SelectedDevice_ResponseError('Video scan: Wait for stop', err)
        except (ConnectionResetError, RuntimeError) as err:
            self.SelectedDevice_ResponseError('Video scan: Wait for stop', err)

def main():
    app = MyApplication(sys.argv)
    app.mainWindow = MyMainWindow()
    app.mainWindow.show()
    app.exec_()

if (__name__ == '__main__'):
    main()
