import glob
import os
import shutil
import time

import cv2
import ffmpeg
import numpy as np
import pygame
import wavio


class VideoConverter:
    def __init__(self, selections, video_input, audio_samples, fps, audio_rate, audio_sampwidth):
        # selection of frames
        self.selections = np.array([list(x) for x in selections])
        # folder containing jpg frames
        self.video_input = video_input
        # audio samples where we can construct wav file
        self.audio_samples = audio_samples
        # fps
        self.fps = fps
        # audio sampling rate
        self.audio_rate = audio_rate
        # sampling width of audio
        self.audio_sampwidth = audio_sampwidth

    def clear_files(self):
        files = glob.glob('output/*')
        for f in files:
            os.remove(f)

    def get_file_names(self):
        selections = []
        for selection in self.selections:
            for i in range(selection[0], selection[1]):
                selections.append('frame' + str(i) + '.jpg')
        self.selections = selections

    def convert_video(self):
        frames = []
        for filename in self.selections:
            img = cv2.imread(self.video_input + filename)
            height, width, layers = img.shape
            frames.append(img)
        out = cv2.VideoWriter('output/video.mp4',
                              cv2.VideoWriter_fourcc(*'mp4v'), self.fps, (width, height))
        for frame in frames:
            out.write(frame)
        out.release()

    def construct_audio(self, path=None):
        total_frames = np.sum(np.subtract(self.selections[:, 1], self.selections[:, 0]))
        a = np.empty([total_frames * 1600, 2], dtype=np.int16)
        i = 0
        for selection in self.selections:
            start = selection[0]
            end = selection[1]
            audio_slice = self.audio_samples[start * 1600:end * 1600]
            a[i:i + len(audio_slice)] = audio_slice
            i += len(audio_slice)
        wavio.write("output/audio.wav" if path is None else path, a,
                    self.audio_rate, sampwidth=self.audio_sampwidth)

    def merge_audio(self):
        video = ffmpeg.input('output/video.mp4')
        audio = ffmpeg.input('output/audio.wav')
        out = ffmpeg.output(video, audio, 'output/summarized_video.mp4')
        out.run()

    def offline_conversion(self, folder_path):
        jpg_folder_path = folder_path + '/frames/'
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
            os.mkdir(jpg_folder_path)
        else:
            shutil.rmtree(folder_path, ignore_errors=True)
            os.mkdir(folder_path)
            os.mkdir(jpg_folder_path)
        # construct and convert the audio
        self.construct_audio(folder_path + '/audio.wav')
        # convert frame selections into file names
        self.get_file_names()
        # copy all selected frames into the frames folder
        for filename in self.selections:
            shutil.copy(self.video_input + filename, jpg_folder_path + filename)

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

    # play audio and display frames with an interval
    def play(self):

        self.construct_audio()
        self.get_file_names()

        # pygame.mixer.pre_init(frequency=44100)
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load("output/audio.wav")
        # play once
        pygame.mixer.music.play(0)

        # display image
        display_width = 320
        display_height = 180

        clock = pygame.time.Clock()
        pause = False

        gameDisplay = pygame.display.set_mode((display_width, display_height))
        pygame.display.set_caption('Summarized Video')

        x = 0
        y = 0

        folder = self.video_input

        filename = "/frame"
        frame_num = 0
        frame_format = ".jpg"

        # control play speed
        play_fps = self.fps
        fps_step = 5
        prev_fps_incr = False

        start_time = time.time()
        # while (os.path.exists(folder + filename + str(frame_num) + frame_format)):

        # image = pygame.image.load(folder + "frame0.jpg")

        # for frame in self._selections:
        while frame_num < len(self.selections):

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        if pause:
                            pause = False
                            start_time += time.time() - start_pause
                            if not pygame.mixer.music.get_busy():
                                pygame.mixer.music.unpause()
                        else:
                            pause = True
                            start_pause = time.time()
                            if pygame.mixer.music.get_busy():
                                pygame.mixer.music.pause()

            if not pause:
                img = pygame.image.load(folder + self.selections[frame_num])
                gameDisplay.blit(img, (x, y))

                pygame.display.update()

                # wait twice as long for every 100th frame to achieve 30 fps (33.33ms/frame), otherwise wait for 33ms
                if frame_num % 100 != 0:
                    clock.tick(play_fps)
                else:
                    clock.tick(play_fps / 2)

                end_time = time.time()

                # change fps if too fast/slow
                if frame_num % 100 != 0:

                    if end_time - start_time < 1 / 30.0 * frame_num:

                        if prev_fps_incr:
                            fps_step = 5
                        else:
                            fps_step = fps_step / 2
                        play_fps -= fps_step
                        prev_fps_incr = False

                    elif end_time - start_time > 1 / 30.0 * frame_num:

                        if not prev_fps_incr:
                            fps_step = 5
                        else:
                            fps_step = fps_step / 2
                        play_fps += fps_step
                        prev_fps_incr = True

                frame_num += 1

        pygame.quit()
