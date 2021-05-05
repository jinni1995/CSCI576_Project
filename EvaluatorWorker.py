import time

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

        print('Program ran for {time_taken} mins'.format(time_taken=round(total_time / 60., 2)))
        self.signals.finished_with_results.emit((frame_nums_to_write, evaluator.audio))
