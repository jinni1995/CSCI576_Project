#!/usr/bin/env python3

import os
import re
from collections import OrderedDict

import face_recognition
import imutils
import numpy as np
import wavio
from blockmatching import *
from scenedetect.detectors import ContentDetector

from shot import Shot
from video_converter import VideoConverter


class Evaluator:
    def __init__(self, frame_path, audio_path, signals):
        self.rgb_folder = frame_path
        self.audio = wavio.read(audio_path)
        self.frames = None
        self.cutting_list = None
        self.shots = None
        self.signals = signals
        # detect scenes and read frames
        self.detect_scenes()
        # segregate shots
        self.get_shots()

    def detect_scenes(self):
        filenames = os.listdir(self.rgb_folder)
        filenames.sort(key=lambda x: int(re.sub('\D', '', x)))
        detector = ContentDetector(threshold=30.0, min_scene_len=7)
        self.cutting_list = []
        self.frames = []

        frame_num = 0
        for filename in filenames:
            with open(self.rgb_folder + filename, 'rb') as f:
                bytes = bytearray(f.read())
            bytes = np.array(bytes)
            frame_img = np.dstack([bytes[0:320 * 180], bytes[320 * 180: 320 * 180 * 2], bytes[320 * 180 * 2:]])
            frame_img = frame_img.reshape(180, 320, 3)
            self.frames.append(frame_img)
            cuts = detector.process_frame(frame_num, frame_img)
            self.cutting_list += cuts
            frame_num += 1
            if frame_num % 1000 == 0 and self.signals is not None:
                self.signals.report_progress.emit((
                    'Detecting and segmenting shots... {frame_num}/16200 frames evaluated.'.format(
                        frame_num=frame_num), frame_num / 16200))
        self.cutting_list += detector.post_process(frame_num)
        self.frames = self.frames

    def get_shots(self):
        shots = []
        i = 0
        s = 0
        for frame in self.cutting_list:
            shot = Shot(num=s, start=i, end=frame)
            shots.append(shot)
            s += 1
            i = frame
        if i < 16200:
            shot = Shot(num=s, start=i, end=16200)
            shots.append(shot)
        self.shots = shots

    def evaluate(self):
        # param for motion evaluation
        alpha = .01

        # param for audio evaluation
        samples = self.audio.data

        for shot in self.shots:
            # get frames corresponding to the current shot
            shot_frames = np.array(self.frames[shot.start: shot.end])
            # evaluate motion
            first_frame = True
            background = None
            old_frame = None
            motion_scores = {}
            for idx, frame in enumerate(shot_frames):
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
                        motion_scores[
                            str(shot.start + idx - 1) + '_' + str(
                                shot.start + idx)] = self.get_motion_score_of_two_frames(
                            np.array(meand))
                    else:
                        motion_scores[str(shot.start + idx - 1) + '_' + str(shot.start + idx)] = 0.
            shot.motion_scores = motion_scores
            shot.motion_score = shot.get_motion_score()

            # evaluate audio
            shot_audio_samples = samples[shot.start * 1600:shot.end * 1600]
            shot.audio_score = np.average(shot_audio_samples)

            # evaluate faces
            subsampled_frames = shot_frames[
                np.random.choice(shot_frames.shape[0], int(shot_frames.shape[0] * .2), replace=False)]
            for frame in subsampled_frames:
                faces = face_recognition.face_locations(frame)
                if faces:
                    shot.face_detected = True
                    break
            if shot.num % 10 == 0 and self.signals is not None:
                self.signals.report_progress.emit((
                    'Evaluating shots and calculating scores... {shot_num}/{shots} shots evaluated.'.format(
                        shot_num=shot.num, shots=len(self.shots)), shot.num / len(self.shots)))

        # normalize scores
        audio_scores = np.array([shot.audio_score for shot in self.shots])
        norm_audio_scores = audio_scores / np.linalg.norm(audio_scores)
        avg_audio_score = np.average(norm_audio_scores)

        for shot in self.shots:
            shot.audio_score = norm_audio_scores[shot.num]
            shot.get_shot_score(avg_audio_score)
        if self.signals is not None:
            self.signals.report_progress.emit((
                'Evaluating shots and calculating scores... {shot_num}/{shots} shots evaluated.'.format(
                    shot_num=len(self.shots), shots=len(self.shots)), 1))

    def get_motion_score_of_two_frames(self, meand):
        return sum(np.sqrt(np.square(meand[:, 0]) + np.square(meand[:, 1]))) / meand.shape[0]

    def select_frames(self):
        scores = [shot.shot_score for shot in self.shots]
        shot_nums = [i for i in range(0, len(self.shots))]
        shot_scores = dict(zip(shot_nums, scores))
        sorted_shot_scores = OrderedDict(sorted(shot_scores.items(), key=lambda item: item[1], reverse=True))
        fps = 30
        # min of 89 seconds
        seconds = 89
        min_frames = fps * seconds
        num_selected_frames = 0
        frame_nums_to_write = []
        frames = []
        for k, v in sorted_shot_scores.items():
            shot = self.shots[k]
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
    folder = 'test_data_3'
    video_name = 'test_video_3'
    frames_rgb_folder = 'input/test_dataset/{folder}/frames_rgb_test/{video_name}/'.format(folder=folder,
                                                                                           video_name=video_name)
    frames_jpg_folder = 'input/test_dataset/{folder}/frames_test/{video_name}/'.format(folder=folder,
                                                                                        video_name=video_name)
    audio_file = 'input/test_dataset/{folder}/{video_name}.wav'.format(folder=folder, video_name=video_name)

    evaluator = Evaluator(frames_rgb_folder, audio_file, None)
    evaluator.evaluate()
    frame_nums_to_write = evaluator.select_frames()

    # offline run
    converter = VideoConverter(frame_nums_to_write, frames_jpg_folder, evaluator.audio.data, 30, evaluator.audio.rate,
                               evaluator.audio.sampwidth)
    converter.offline_conversion('./output_offline/{video_name}'.format(video_name=video_name))
