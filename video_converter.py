import glob
import os

import cv2
import ffmpeg
import numpy as np
import wavio


class VideoConverter:
    def __init__(self, selections, video_input, audio_samples, fps, audio_rate, audio_sampwidth):
        # selection of frames
        self._selections = np.array([list(x) for x in selections])
        # folder containing jpg frames
        self._video_input = video_input
        # audio samples where we can construct wav file
        self._audio_samples = audio_samples
        # fps
        self._fps = fps
        # audio sampling rate
        self._audio_rate = audio_rate
        # sampling width of audio
        self._audio_sampwidth = audio_sampwidth

    def clear_files(self):
        files = glob.glob('output/*')
        for f in files:
            os.remove(f)

    def get_file_names(self):
        selections = []
        for selection in self._selections:
            for i in range(selection[0], selection[1]):
                selections.append('frame' + str(i) + '.jpg')
        self._selections = selections

    def convert_video(self):
        frames = []
        for filename in self._selections:
            img = cv2.imread(self._video_input + filename)
            height, width, layers = img.shape
            frames.append(img)
        out = cv2.VideoWriter('output/video.mp4',
                              cv2.VideoWriter_fourcc(*'mp4v'), self._fps, (width, height))
        for frame in frames:
            out.write(frame)
        out.release()

    def construct_audio(self):
        total_frames = np.sum(np.subtract(self._selections[:, 1], self._selections[:, 0]))
        a = np.empty([total_frames * 1600, 2], dtype=np.int16)
        i = 0
        for selection in self._selections:
            start = selection[0]
            end = selection[1]
            audio_slice = self._audio_samples[start * 1600:end * 1600]
            a[i:i + len(audio_slice)] = audio_slice
            i += len(audio_slice)
        wavio.write("output/audio.wav", a,
                    self._audio_rate, sampwidth=self._audio_sampwidth)

    def merge_audio(self):
        video = ffmpeg.input('output/video.mp4')
        audio = ffmpeg.input('output/audio.wav')
        out = ffmpeg.output(video, audio, 'output/summarized_video.mp4')
        out.run()

    def convert(self):
        # delete all files in output folder
        self.clear_files()
        # construct and convert the audio
        self.construct_audio()
        # convert selected list of frame numbers to file names of the jpg frames
        self.get_file_names()
        # convert the frames to a video
        self.convert_video()
        # merge audio and video
        self.merge_audio()
