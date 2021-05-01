#!/usr/bin/env python3

import os
import sys
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QLabel, QProgressBar, QWidget, QFileDialog, QPushButton, QVBoxLayout, QGroupBox, QHBoxLayout

import time
import threading
from main import Evaluator

from blockmatching import *

from video_converter import VideoConverter

class Gui(QWidget):

    def __init__(self: 'Gui'):
        super().__init__()
        self.title = 'CSCI 576 Final Project'
        self.left = 0
        self.top = 0
        self.width = 1920
        self.height = 1080

        self.jpgFolder = None
        self.rgbFolder = None
        self.wavFile = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Evaluator Progress Bar
        self.evaluator_progress_bar = self.createProgressBarPercent()

        # Box Layout
        self.windowLayout = QVBoxLayout()

        # Add Choose buttons
        self.windowLayout.addWidget(self.createChooseButtons())

        # Set layout and show
        self.setLayout(self.windowLayout)
        self.show()

    def createVideoEvaluatorSection(self: 'Gui') -> QGroupBox:
        groupBox = QGroupBox('Video Evaluator')
        groupBox.setFixedHeight(125)

        layout = QVBoxLayout()
        self.evaluatorProgressLabel = QLabel('Press the button to evaluate the video')
        layout.addWidget(self.createButton('Evaluate Video', self.evaulate_video))
        layout.addWidget(self.evaluator_progress_bar)
        layout.addWidget(self.evaluatorProgressLabel)

        groupBox.setLayout(layout)

        return groupBox

    def addVideoEvaluatorSection(self: 'Gui'):
        if self.jpgFolder is not None and self.rgbFolder is not None and self.wavFile is not None:
            self.windowLayout.addWidget(self.createVideoEvaluatorSection())

    def createProgressBarPercent(self: 'Gui') -> QProgressBar:
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        return progress_bar

    def createChooseButtons(self: 'Gui') -> QGroupBox:
        chooseButtonsGroupBox = QGroupBox("Choose your JPG, RGB, and WAV Files/Folders")
        chooseButtonsGroupBox.setFixedHeight(100)
        layout = QHBoxLayout()

        jpgBox = QVBoxLayout()
        self.jpgLabel = QLabel()
        jpgBox.addWidget(self.createButton('Choose JPG Folder', self.setJpgFolder))
        jpgBox.addWidget(self.jpgLabel)
        layout.addLayout(jpgBox)

        rgbBox = QVBoxLayout()
        self.rgbLabel = QLabel()
        rgbBox.addWidget(self.createButton('Choose RGB Folder', self.setRgbFolder))
        rgbBox.addWidget(self.rgbLabel)
        layout.addLayout(rgbBox)

        wavBox = QVBoxLayout()
        self.wavLabel = QLabel()
        wavBox.addWidget(self.createButton('Choose WAV File', self.setWavFile))
        wavBox.addWidget(self.wavLabel)
        layout.addLayout(wavBox)

        chooseButtonsGroupBox.setLayout(layout)

        return chooseButtonsGroupBox

    def createButton(self: 'Gui', label: str, callback) -> QPushButton:
        button = QPushButton(label, self)
        button.clicked.connect(callback)
        return button


    @pyqtSlot()
    def setJpgFolder(self: 'Gui'):
        self.jpgFolder = self.getFolderPathDialog('JPG Folder') + '/'
        self.jpgLabel.setText('/'.join(self.jpgFolder.split('/')[-5:]))
        self.addVideoEvaluatorSection()

    @pyqtSlot()
    def setRgbFolder(self: 'Gui'):
        self.rgbFolder = self.getFolderPathDialog('RGB Folder') + '/'
        self.rgbLabel.setText('/'.join(self.rgbFolder.split('/')[-5:]))
        self.addVideoEvaluatorSection()

    @pyqtSlot()
    def setWavFile(self: 'Gui'):
        self.wavFile = self.getFilePathDialog('WAV File', 'WAV Audio Files (*.wav)')
        self.wavLabel.setText('/'.join(self.wavFile.split('/')[-5:]))
        self.addVideoEvaluatorSection()

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
        evaluator_thread = threading.Thread(target=self.evaluate_video_thread_function)
        evaluator_thread.start()

    def setProgress(self: 'Gui', label: str, percentComplete: float):
        progress = max(min(100, round(100 * percentComplete)), 0)

        self.evaluatorProgressLabel.setText(label)

        # Trying this to prevent obscure error
        time.sleep(1)

        self.evaluator_progress_bar.setValue(progress)

    def evaluate_video_thread_function(self: 'Gui'):
        total_time = 0.
        predicted_time = 5. * 60.

        start_time = time.time()
        self.setProgress('Starting video evaluation', 0)
        self.evaluator = Evaluator(self.rgbFolder, self.wavFile)
        end_time = time.time()
        total_time += end_time - start_time
        self.setProgress('Detected and segmented shots in ' + str(end_time - start_time) + 's', total_time / predicted_time)

        start_time = time.time()
        self.evaluator.evaluate()
        end_time = time.time()
        total_time += end_time - start_time
        self.setProgress('Evaluated video in ' + str(end_time - start_time) + 's', total_time / predicted_time)

        start_time = time.time()
        frame_nums_to_write = self.evaluator.select_frames()
        end_time = time.time()
        total_time += end_time - start_time
        self.setProgress('Selected frames in ' + str(end_time - start_time) + 's', total_time / predicted_time)

        self.setProgress('Program ran for ' + str(total_time) + ' seconds/' + str(total_time / 60.) + ' mins', total_time / predicted_time)

        # TODO remove this once we have the video player ready
        self.setProgress('Converting selected frames into video...', total_time / predicted_time)
        converter = VideoConverter(frame_nums_to_write, self.jpgFolder, self.evaluator.audio.data, 30, self.evaluator.audio.rate,
                                self.evaluator.audio.sampwidth)
        converter.convert()
        self.setProgress('Completed evaluating video', 1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Gui()
    sys.exit(app.exec_())