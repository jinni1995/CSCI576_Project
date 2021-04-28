import os
import re
import sys
import time
from collections import OrderedDict

import face_recognition
import imutils
import numpy as np
import wavio
from blockmatching import *
from scenedetect.detectors import ContentDetector

from shot import Shot
from video_converter import VideoConverter

np.set_printoptions(threshold=sys.maxsize)


class Evaluator:
    def __init__(self, frame_path, audio_path):
        self.rgb_folder = frame_path
        self.audio = wavio.read(audio_path)
        self.frames = None
        self.cutting_list = None
        self.shots = None

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

    def get_motion_score_of_two_frames(self, meand):
        return sum(np.sqrt(np.square(meand[:, 0]) + np.square(meand[:, 1]))) / meand.shape[0]

    def evaluate_motion(self):
        alpha = 0.01

        shot_scores = {}
        for shot in self.shots:
            first_frame = True
            background = None
            old_frame = None
            i = shot.start + 1
            motion_scores = {}
            for frame in self.frames[shot.start: shot.end]:
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
        self.shot_scores = shot_scores

    def evaluate_audio(self):
        samples = self.audio.data
        # average audio level of the entire level
        avg_audio_amplitude = np.average(samples)
        audio_scores = np.zeros(len(self.shots), dtype=np.float64)
        i = 0
        for shot in self.shots:
            shot_audio_samples = samples[shot.start * 1600:shot.end * 1600]
            audio_scores[i] = np.average(shot_audio_samples)
            i += 1
        # normalize the scores
        norm_audio_scores = audio_scores / np.linalg.norm(audio_scores)
        i = 0
        for shot in self.shots:
            shot.audio_score = norm_audio_scores[i]
            i += 1

    def evaluate_faces(self):
        for shot in self.shots:
            faces = []
            shot_frames = np.array(self.frames[shot.start: shot.end])
            # we will subsample only 20% of the frames to do face detection
            # after testing with various subsampling percentages, we found that subsampling by 50%
            # only manages to detect faces in 2 to 11 more shots but the time taken is exponentially
            # increased by >2 minutes
            subsampled_frames = shot_frames[
                np.random.choice(shot_frames.shape[0], int(shot_frames.shape[0] * .2), replace=False)]
            for frame in subsampled_frames:
                faces = face_recognition.face_locations(frame)
            if faces:
                # if there are faces detected, then it means that faces must appear so often in that shot that we can
                # detect it even with a mere 20% sampling of frames
                shot.face_detection_score = 1

    def select_frames(self):
        sorted_shot_scores = OrderedDict(sorted(self.shot_scores.items(), key=lambda item: item[1], reverse=True))
        fps = 30
        # min of 85 seconds
        seconds = 85
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
    video_name = 'soccer'
    frames_rgb_folder = 'input/project_dataset/frames_rgb/{video_name}/'.format(video_name=video_name)
    frames_jpg_folder = 'input/project_dataset/frames/{video_name}/'.format(video_name=video_name)
    audio_file = 'input/project_dataset/audio/{video_name}.wav'.format(video_name=video_name)
    total_time = 0.

    start_time = time.time()
    evaluator = Evaluator(frames_rgb_folder, audio_file)
    evaluator.detect_scenes()
    end_time = time.time()
    print('Detected shots in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    start_time = time.time()
    evaluator.get_shots()
    end_time = time.time()
    print('Retrieved shots in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    start_time = time.time()
    evaluator.evaluate_faces()
    end_time = time.time()
    print('Detected faces in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    start_time = time.time()
    evaluator.evaluate_audio()
    end_time = time.time()
    print('Evaluated audio in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    start_time = time.time()
    evaluator.evaluate_motion()
    end_time = time.time()
    print('Evaluated motion in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    start_time = time.time()
    frame_nums_to_write = evaluator.select_frames()
    end_time = time.time()
    print('Selected frames in ' + str(end_time - start_time) + 's')
    total_time += end_time - start_time

    print('Program ran for ' + str(total_time) + ' seconds/' + str(total_time / 60.) + ' mins')

    print('Converting selected frames into video...')
    converter = VideoConverter(frame_nums_to_write, frames_jpg_folder, evaluator.audio.data, 30, evaluator.audio.rate,
                               evaluator.audio.sampwidth)
    converter.convert()
