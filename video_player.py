import os
import re
import time

import pygame


class VideoPlayer:
    def __init__(self, video_input, audio_samples, fps):
        # folder containing jpg frames
        self.video_input = video_input
        # audio samples where we can construct wav file
        self.audio_samples = audio_samples
        # fps
        self.fps = fps

    # play audio and display frames with an interval
    def play(self):

        # self.construct_audio()
        # self.get_file_names()

        # pygame.mixer.pre_init(frequency=44100)
        pygame.init()

        # display image
        display_width = 320
        display_height = 180

        clock = pygame.time.Clock()
        crashed = False
        pause = False

        gameDisplay = pygame.display.set_mode((display_width, display_height))
        pygame.display.set_caption('video')

        x = 0
        y = 0

        folder = self.video_input

        # control play speed
        play_fps = self.fps
        fps_step = 5
        prev_fps_incr = False

        pygame.mixer.init()
        pygame.mixer.music.load(self.audio_samples)
        # play once
        pygame.mixer.music.play(0)

        filenames = os.listdir(self.video_input)
        filenames.sort(key=lambda x: int(re.sub('\D', '', x)))

        start_time = time.time()
        frame_num = 0
        for filename in filenames:
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
                img = pygame.image.load(folder + filename)
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
