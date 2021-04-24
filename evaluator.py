import os
import re
import sys
import time
from collections import OrderedDict

import imutils
import numpy as np
import wavio
from blockmatching import *
from scenedetect.detectors import ContentDetector

from shot import Shot
from video_converter import VideoConverter

np.set_printoptions(threshold=sys.maxsize)


class Evaluator:
    def __init__(self, folder, audio_samples, frames=None):
        self._folder = folder
        self._frames = frames
        self._audio_samples = audio_samples
        self._cutting_list = None

    def detect_scenes(self):
        filenames = os.listdir(self._folder)
        filenames.sort(key=lambda f: int(re.sub("\D", "", f)))
        detector = ContentDetector(threshold=30.0, min_scene_len=7)
        cutting_list = []
        images = []

        frame_num = 0
        for filename in filenames:
            with open(self._folder + filename, 'rb') as f:
                bytes = bytearray(f.read())
            bytes = np.array(bytes)
            frame_img = np.dstack([bytes[0:320 * 180], bytes[320 * 180: 320 * 180 * 2], bytes[320 * 180 * 2:]])
            frame_img = frame_img.reshape(180, 320, 3)
            images.append(frame_img)
            cuts = detector.process_frame(frame_num, frame_img)
            cutting_list += cuts
            frame_num += 1
        cutting_list += detector.post_process(frame_num)
        self._frames = images
        self._cutting_list = cutting_list
        return images, cutting_list

    def get_shots(self):
        shots = []
        i = 0
        s = 0
        for frame in self._cutting_list:
            shot = Shot(num=s, start=i, end=frame)
            shots.append(shot)
            s += 1
            i = frame
        if i < len(images):
            shot = Shot(num=s, start=i, end=16200)
            shots.append(shot)
        self._shots = shots

    def get_motion_score_of_two_frames(self, meand):
        return sum(np.sqrt(np.square(meand[:, 0]) + np.square(meand[:, 1]))) / meand.shape[0]

    def evaluate_motion(self):
        # TODO tune this parameter
        alpha = 0.01

        shot_scores = {}
        for shot in self._shots:
            first_frame = True
            background = None
            old_frame = None
            i = shot.start + 1
            motion_scores = {}
            for frame in self._frames[shot.start: shot.end]:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame = imutils.resize(frame, width=160, height=90)
                if first_frame:
                    background = BackgroundSubtractor(alpha, frame)
                    foreground = background.foreground(frame)
                    old_frame = foreground.copy()
                    first_frame = False
                else:
                    foreground = background.foreground(frame)
                    XP, YP, XD, YD = block_matching(old_frame, foreground, 4, 4)
                    U, V, object_tops, meand = clustering(XD, YD, XP, YP)
                    old_frame = foreground.copy()
                    if meand:
                        motion_scores[str(i - 1) + '_' + str(i)] = self.get_motion_score_of_two_frames(np.array(meand))
                    else:
                        motion_scores[str(i - 1) + '_' + str(i)] = 0.
                    i += 1
            shot.motion_scores = motion_scores
            shot.motion_score = shot.get_motion_score()
            shot.shot_score = shot.get_shot_score()
            shot_scores[shot.num] = shot.shot_score
        return shot_scores

    def evaluate_audio(self):
        samples = self._audio_samples.data
        # average audio level of the entire level
        avg_audio_amplitude = np.average(samples)
        audio_scores = np.zeros(len(self._shots), dtype=np.float64)
        i = 0
        for shot in self._shots:
            shot_audio_samples = samples[shot.start * 1600:shot.end * 1600]
            audio_scores[i] = np.average(shot_audio_samples)
            i += 1
        # normalize the scores
        norm_audio_scores = audio_scores / np.linalg.norm(audio_scores)
        i = 0
        for shot in self._shots:
            shot.audio_score = norm_audio_scores[i]
            i += 1

    def select_frames(self, shot_scores):
        sorted_shot_scores = OrderedDict(sorted(shot_scores.items(), key=lambda item: item[1], reverse=True))
        fps = 30
        # min of 85 seconds
        seconds = 85
        min_frames = fps * seconds
        num_selected_frames = 0
        frame_nums_to_write = []
        frames = []
        for k, v in sorted_shot_scores.items():
            shot = self._shots[k]
            start, end = shot.get_frames_with_highest_score()
            if start is not None:
                frame_nums_to_write.append((start, end))
                num_selected_frames += (end - start)
                frames.append(end - start)
            if num_selected_frames >= min_frames:
                break
        frame_nums_to_write.sort(key=lambda x: x[0])
        return frame_nums_to_write


if __name__ == "__main__":
    frames_rgb_folder = 'input/project_dataset/frames_rgb/soccer/'
    frames_jpg_folder = 'input/project_dataset/frames/soccer/'
    audio_file = 'input/project_dataset/audio/soccer.wav'
    total_time = 0.

    audio = wavio.read(audio_file)

    start_time = time.time()
    evaluator = Evaluator(frames_rgb_folder, audio)
    images, cutting_list = evaluator.detect_scenes()
    end_time = time.time()
    print('Detected shots in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    start_time = time.time()
    evaluator.get_shots()
    end_time = time.time()
    print('Retrieved shots in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    start_time = time.time()
    evaluator.evaluate_audio()
    end_time = time.time()
    print('Evaluated audio in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    start_time = time.time()
    shot_scores = evaluator.evaluate_motion()
    end_time = time.time()
    print('Evaluated motion in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    start_time = time.time()
    frame_nums_to_write = evaluator.select_frames(shot_scores=shot_scores)
    end_time = time.time()
    print('Selected frames in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    print('Program ran for ' + str(total_time) + ' seconds/' + str(total_time / 60.) + ' mins')

    print('Converting selected frames into video...')
    converter = VideoConverter(frame_nums_to_write, frames_jpg_folder, audio.data, 30, audio.rate, audio.sampwidth)
    converter.convert()
