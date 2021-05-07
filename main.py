#!/usr/bin/env python3
import os
import sys
import time
from typing import Tuple

from PyQt5.QtCore import QThreadPool, pyqtSlot
from PyQt5.QtWidgets import QApplication, QLabel, QProgressBar, QWidget, QFileDialog, QPushButton, QVBoxLayout, \
    QGroupBox, QHBoxLayout
from pynput.keyboard import Controller
from wavio import Wav

from EvaluatorWorker import EvaluatorWorker
from video_converter import VideoConverter
from video_player import VideoPlayer


class Gui(QWidget):

    def __init__(self: 'Gui'):
        super().__init__()
        self.title = 'CSCI 576 Final Project'
        self.left = 0
        self.top = 0
        self.width = 1000
        self.height = 360

        self.jpgFolder = None
        self.rgbFolder = None
        self.wavFile = None

        self.playJpgFolder = None
        self.playWavFile = None

        self.threadpool = QThreadPool()

        self.playing_video = False
        self.video_paused = False

        self.keyboard_emulator = Controller()

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Evaluator Progress Bar
        self.evaluator_progress_bar = self.createProgressBarPercent()

        # Box Layout
        self.windowLayout = QVBoxLayout()

        # Options are to choose folders for video evaluation or play existing video
        self.online_mode_widget = self.createOnlineModeButtons()
        self.offline_mode_widget = self.createOfflineModeButtons()

        # Add buttons
        self.windowLayout.addWidget(self.online_mode_widget)
        self.windowLayout.addWidget(self.offline_mode_widget)

        # Set layout and show
        self.setLayout(self.windowLayout)
        self.show()

    def createProgressBarPercent(self: 'Gui') -> QProgressBar:
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        return progress_bar

    def createOnlineModeButtons(self: 'Gui') -> QGroupBox:
        onlineModeGroup = QGroupBox("Choose your JPG, RGB, and WAV Files/Folders for video evaluation")
        onlineModeGroup.setFixedHeight(250)

        groupLayout = QVBoxLayout()

        pathLayout = QHBoxLayout()
        jpgBox = QVBoxLayout()
        self.jpgLabel = QLabel()
        jpgBox.addWidget(self.createButton('Choose JPG Folder', self.setJpgFolder))
        jpgBox.addWidget(self.jpgLabel)
        pathLayout.addLayout(jpgBox)

        rgbBox = QVBoxLayout()
        self.rgbLabel = QLabel()
        rgbBox.addWidget(self.createButton('Choose RGB Folder', self.setRgbFolder))
        rgbBox.addWidget(self.rgbLabel)
        pathLayout.addLayout(rgbBox)

        wavBox = QVBoxLayout()
        self.wavLabel = QLabel()
        wavBox.addWidget(self.createButton('Choose WAV File', self.setWavFile))
        wavBox.addWidget(self.wavLabel)
        pathLayout.addLayout(wavBox)
        groupLayout.addLayout(pathLayout)

        evalLayout = QHBoxLayout()
        evalBox = QVBoxLayout()
        self.evaluatorProgressLabel = QLabel()
        evalBox.addWidget(self.createButton('Evaluate Video', self.evaulate_video))
        evalBox.addWidget(self.evaluator_progress_bar)
        evalBox.addWidget(self.evaluatorProgressLabel)
        evalLayout.addLayout(evalBox)
        groupLayout.addLayout(evalLayout)

        playLayout = QHBoxLayout()
        playBox = QVBoxLayout()
        self.play_converted_video_button = self.createButton('Play', self.play_converted_video)
        playBox.addWidget(self.play_converted_video_button)
        playLayout.addLayout(playBox)
        groupLayout.addLayout(playLayout)

        onlineModeGroup.setLayout(groupLayout)

        return onlineModeGroup

    @pyqtSlot()
    def setJpgFolder(self: 'Gui'):
        self.jpgFolder = self.getFolderPathDialog('JPG Folder') + '/'
        self.jpgLabel.setText('/'.join(self.jpgFolder.split('/')[-5:]))

    @pyqtSlot()
    def setRgbFolder(self: 'Gui'):
        self.rgbFolder = self.getFolderPathDialog('RGB Folder') + '/'
        self.rgbLabel.setText('/'.join(self.rgbFolder.split('/')[-5:]))

    @pyqtSlot()
    def setWavFile(self: 'Gui'):
        self.wavFile = self.getFilePathDialog('WAV File', 'WAV Audio Files (*.wav)')
        self.wavLabel.setText('/'.join(self.wavFile.split('/')[-4:]))

    def createOfflineModeButtons(self: 'Gui') -> QGroupBox:
        groupBox = QGroupBox("Or choose your JPG Folder and WAV File for Video Play")
        groupBox.setFixedHeight(100)
        layout = QHBoxLayout()

        jpgBox = QVBoxLayout()
        self.playJpgLabel = QLabel()
        jpgBox.addWidget(self.createButton('Choose JPG Folder', self.setPlayJpgFolder))
        jpgBox.addWidget(self.playJpgLabel)
        layout.addLayout(jpgBox)

        wavBox = QVBoxLayout()
        self.playWavLabel = QLabel()
        wavBox.addWidget(self.createButton('Choose WAV File', self.setPlayWavFile))
        wavBox.addWidget(self.playWavLabel)
        layout.addLayout(wavBox)

        playBox = QVBoxLayout()
        self.play_video_button = self.createButton('Play', self.play_video)
        playBox.addWidget(self.play_video_button)
        playBox.addWidget(QLabel())
        layout.addLayout(playBox)

        groupBox.setLayout(layout)

        return groupBox

    @pyqtSlot()
    def play_video(self: 'Gui'):
        if not self.playing_video:
            self.playing_video = True
            self.video_player = VideoPlayer(self.playJpgFolder, self.playWavFile, 30)
            self.play_video_button.setText('Pause')
            self.video_player.play()
            self.play_video_button.setText('Play')
            self.playing_video = False
        else:
            self.keyboard_emulator.press('p')
            self.keyboard_emulator.release('p')
            self.video_paused = not self.video_paused
            if self.video_paused:
                self.play_video_button.setText('Play')
            else:
                self.play_video_button.setText('Pause')

    @pyqtSlot()
    def setPlayJpgFolder(self: 'Gui'):
        self.playJpgFolder = self.getFolderPathDialog('JPG Folder') + '/'
        self.playJpgLabel.setText('/'.join(self.playJpgFolder.split('/')[-4:]))

    @pyqtSlot()
    def setPlayWavFile(self: 'Gui'):
        self.playWavFile = self.getFilePathDialog('WAV File', 'WAV Audio Files (*.wav)')
        self.playWavLabel.setText('/'.join(self.playWavFile.split('/')[-3:]))

    def createButton(self: 'Gui', label: str, callback) -> QPushButton:
        button = QPushButton(label, self)
        button.clicked.connect(callback)
        return button

    def getFolderPathDialog(self: 'Gui', caption: str) -> str or None:
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        dirname = QFileDialog.getExistingDirectory(self, caption, directory=os.getcwd(), options=options)
        return dirname

    def getFilePathDialog(self: 'Gui', caption: str, filter: str) -> str or None:
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, caption, directory=os.getcwd(), filter=filter, options=options)
        return fileName

    @pyqtSlot()
    def evaulate_video(self: 'Gui'):
        worker = EvaluatorWorker(self.rgbFolder, self.wavFile)
        worker.signals.finished_with_results.connect(self.evaluation_complete)
        worker.signals.report_progress.connect(self.setProgress)
        self.threadpool.start(worker)

    def setProgress(self: 'Gui', information: Tuple[str, float]):
        label = information[0]
        percentComplete = information[1]
        progress = max(min(100, round(100 * percentComplete)), 0)
        print(label)
        print(progress)

        self.evaluatorProgressLabel.setText(label)

        # Trying this to prevent obscure error
        time.sleep(1)

        self.evaluator_progress_bar.setValue(progress)

    def evaluation_complete(self: 'Gui', information: Tuple[list, Wav]):
        frame_nums_to_write = information[0]
        audio = information[1]
        self.frame_nums_to_write = frame_nums_to_write
        self.audio = audio

    def play_converted_video(self: 'Gui'):
        self.converter.play()

    @pyqtSlot()
    def play_converted_video(self: 'Gui'):
        if not self.playing_video:
            self.playing_video = True
            converter = VideoConverter(self.frame_nums_to_write, self.jpgFolder, self.audio.data, 30, \
                                       self.audio.rate, self.audio.sampwidth)
            self.play_converted_video_button.setText('Pause')
            converter.play()
            self.play_converted_video_button.setText('Play')
            self.playing_video = False
        else:
            self.keyboard_emulator.press('p')
            self.keyboard_emulator.release('p')
            self.video_paused = not self.video_paused
            if self.video_paused:
                self.play_converted_video_button.setText('Play')
            else:
                self.play_converted_video_button.setText('Pause')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Gui()
    sys.exit(app.exec_())
