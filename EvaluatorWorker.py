import time

# from video_converter import VideoConverter
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

from evaluator import Evaluator


class Signals(QObject):
    finished_with_results = pyqtSignal(tuple)
    report_progress = pyqtSignal(tuple)


class EvaluatorWorker(QRunnable):

    def __init__(self: 'EvaluatorWorker', rgbFolder: str, wavFile: str):
        super(EvaluatorWorker, self).__init__()
        self.rgbFolder = rgbFolder
        self.wavFile = wavFile
        self.signals = Signals()

    @pyqtSlot()
    def run(self: 'EvaluatorWorker'):
        total_time = 0.
        predicted_time = 5. * 60.

        start_time = time.time()
        self.signals.report_progress.emit(('Detecting and segmenting shots...', 0))
        evaluator = Evaluator(self.rgbFolder, self.wavFile, self.signals)
        end_time = time.time()
        total_time += end_time - start_time

        start_time = time.time()
        evaluator.evaluate()
        end_time = time.time()
        total_time += end_time - start_time

        start_time = time.time()
        frame_nums_to_write = evaluator.select_frames()
        end_time = time.time()
        total_time += end_time - start_time

        self.signals.report_progress.emit(
            ('Program ran for ' + str(round(total_time / 60., 2)) + ' mins', total_time / predicted_time))

        # TODO remove this once we have the video player ready
        # self.signals.report_progress.emit('Converting selected frames into video...', total_time / predicted_time)
        # self.gui.converter = VideoConverter(frame_nums_to_write, self.gui.jpgFolder, evaluator.audio.data, 30, \
        #     evaluator.audio.rate, evaluator.audio.sampwidth)

        # self.converter.convert()

        self.signals.report_progress.emit(('Completed evaluating video', 1))
        self.signals.finished_with_results.emit((frame_nums_to_write, evaluator.audio))
