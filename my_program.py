#!/usr/bin/env python3

import math
import os
import re
import sys
import time

import cv2
import imutils
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import wavio
from scenedetect.detectors import ContentDetector
from scipy.io import wavfile

from motion_detector import MotionDetector
from video_converter import VideoConverter

np.set_printoptions(threshold=sys.maxsize)


def detect_scenes(folder):
    filenames = os.listdir(folder)
    filenames.sort(key=lambda f: int(re.sub("\D", "", f)))
    detector = ContentDetector(threshold=30.0, min_scene_len=7)
    cutting_list = []
    images = []

    frame_num = 0
    for filename in filenames:
        # skip frames to make things faster
        # if frame_num % 2 == 1:
        #     frame_num += 1
        #     continue
        with open(folder + filename, 'rb') as f:
            bytes = bytearray(f.read())
        bytes = np.array(bytes)
        frame_img = np.dstack([bytes[0:320 * 180], bytes[320 * 180: 320 * 180 * 2], bytes[320 * 180 * 2:]])
        frame_img = frame_img.reshape(180, 320, 3)
        images.append(frame_img)
        cuts = detector.process_frame(frame_num, frame_img)
        cutting_list += cuts
        # if frame_num % 100 == 0:
        #     print(frame_num)
        frame_num += 1
    cutting_list += detector.post_process(frame_num)

    return images, cutting_list


def get_shots_and_resize(images, cutting_list):
    shots = []
    i = 0
    s = 0
    for frame in cutting_list:
        s += 1
        shots.append([imutils.resize(x, width=160, height=90) for x in images[i:frame]])
        # shots.append(images[i:frame])
        i = frame
    if i < len(images):
        shots.append([imutils.resize(x, width=160, height=90) for x in images[i:]])
        # shots.append(images[i:])
    print('Shots: ' + str(s))
    return shots


def evaluate_frames(shots):
    frame_weight = {}
    print(len(shots))
    s = 0
    f = 1
    for shot in shots:
        s += 1
        weight_sq = 0
        max_motion_frame_p = 0
        max_motion_frame_c = 1
        for i in range(1, len(shot)):
            start_time = time.time()
            prev = cv2.cvtColor(shot[i - 1], cv2.COLOR_BGR2GRAY)
            curr = cv2.cvtColor(shot[i], cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(prev, curr, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            horz = cv2.normalize(flow[..., 0], None, 0, 255, cv2.NORM_MINMAX)
            vert = cv2.normalize(flow[..., 1], None, 0, 255, cv2.NORM_MINMAX)
            horz = horz.astype('uint8')
            vert = vert.astype('uint8')

            # quantized_h = copy.deepcopy(horz)
            # quantized_v = copy.deepcopy(vert)
            # for n in range(0, 180):
            #     for m in range(0, 320):
            #         quantized_h[n][m] = min([0.0, 127.5, 255], key=lambda x: abs(x - horz[n][m]))
            #         quantized_v[n][m] = min([0.0, 127.5, 255], key=lambda x: abs(x - vert[n][m]))

            quantized_h = horz.flatten()
            quantized_v = vert.flatten()
            levels = np.array([0.0, 127.5, 255])
            quantized_h = np.array([math.floor(levels[(np.abs(levels - el)).argmin()]) for el in quantized_h])
            quantized_v = np.array([math.floor(levels[(np.abs(levels - el)).argmin()]) for el in quantized_v])

            weight = np.count_nonzero(quantized_h != 127) ** 2 + np.count_nonzero(quantized_v != 127) ** 2
            if weight > weight_sq:
                weight_sq = weight
                max_motion_frame_p = i - 1
                max_motion_frame_c = i
            end_time = time.time()
            print(end_time - start_time)
        frame_weight[str(max_motion_frame_p) + "_" + str(max_motion_frame_c)] = weight_sq
    return frame_weight


def evaluate_audio():
    # path of the audio file
    audio_data = 'input/project_dataset/audio/concert.wav'
    x = librosa.load(audio_data, sr=None)
    samplerate, data = wavfile.read(audio_data)
    print(samplerate)
    plt.figure(figsize=(14, 5))
    librosa.display.waveplot(x, sr=None)
    return True


if __name__ == "__main__":
    # modify these paths
    frames_rgb_folder = 'input/project_dataset/frames_rgb/concert/'
    frames_jpg_folder = 'input/project_dataset/frames/concert/'
    audio_file = 'input/project_dataset/audio/concert.wav'

    audio = wavio.read(audio_file)

    start_time = time.time()
    images, cutting_list = detect_scenes(frames_rgb_folder)
    end_time = time.time()
    print(end_time - start_time)

    start_time = time.time()
    detector = MotionDetector(102, images, None)
    events, frame_nums_to_write = detector.scan_motion()
    end_time = time.time()
    print(end_time - start_time)

    print('Converting selected frames into video...')
    converter = VideoConverter(frame_nums_to_write, frames_jpg_folder, audio.data, 30, audio.rate, audio.sampwidth)
    converter.convert()

    # start_time = time.time()
    # shots = get_shots_and_resize(images, cutting_list)
    # end_time = time.time()
    # print(cutting_list)
    # print(end_time - start_time)
    #
    # start_time = time.time()
    # frame_weight = evaluate(shots)
    # print(frame_weight)
    # end_time = time.time()
    # print(end_time - start_time)
