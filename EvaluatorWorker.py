import datetime

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
        start = datetime.datetime.now()
        self.signals.report_progress.emit(('Detecting and segmenting shots...', 0))
        evaluator = Evaluator(self.rgbFolder, self.wavFile, self.signals)
        evaluator.evaluate()
        frame_nums_to_write = evaluator.select_frames()
        end = datetime.datetime.now()

        elapsed = end - start
        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        total_minutes, total_seconds = divmod(remainder, 60)
        total_seconds = '{total_seconds:02d}'.format(total_seconds=int(total_seconds))
        total_minutes = '{total_minutes:02d}'.format(total_minutes=int(total_minutes))

        self.signals.report_progress.emit(('Program ran for {total_minutes}:{total_seconds} (mm:ss)'.format(
            total_minutes=total_minutes, total_seconds=total_seconds), 1))
        self.signals.finished_with_results.emit((frame_nums_to_write, evaluator.audio))
