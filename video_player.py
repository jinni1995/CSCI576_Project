import cv2
import pygame
import os
import time

# class Pause(object):

#     def __init__(self):
#         self.paused = pygame.mixer.music.get_busy()

#     def toggle(self):
#         if self.paused:
#             pygame.mixer.music.unpause()
#         if not self.paused:
#             pygame.mixer.music.pause()
#         self.paused = not self.paused

# Instantiate.

# PAUSE = Pause()

# Detect a key. Call toggle method.

# PAUSE.toggle()

class VideoPlayer:
    def __init__(self, video_input, audio_samples, fps):
        # folder containing jpg frames
        self._video_input = video_input
        # audio samples where we can construct wav file
        self._audio_samples = audio_samples
        # fps
        self._fps = fps

    # load all images from frames dir into an array
    def load_images_from_folder(self, folder):
        images = []
        for filename in sorted(os.listdir(folder)):
            img = cv2.imread(os.path.join(folder,filename))
            if img is not None:
                images.append(img)
        self._frames = images
        # return images

    # play audio and display frames with an interval
    def play(self):

        # self.load_images_from_folder(self._video_input)
        # self._frames.sort()

        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load(self._audio_samples)
        # play once
        pygame.mixer.music.play(0)

        folder = self._video_input

        filename = "/frame"
        frame_num = 0
        frame_format = ".jpg"

        # control play speed
        play_fps = self._fps
        fps_step = 5
        prev_fps_incr = False

        start_time = time.time()
        while (os.path.exists(folder + filename + str(frame_num) + frame_format)):
     
            img = cv2.imread(folder + filename + str(frame_num) + frame_format)
            cv2.imshow("Video", img)

            # wait twice as long for every 100th frame to achieve 30 fps (33.33ms/frame), otherwise wait for 33ms
            if frame_num % 100 != 0 :
                key = cv2.waitKey(int(1 / float(play_fps) * 1000))    
            else :
                key = cv2.waitKey(int(2 / float(play_fps) * 1000))    

            end_time = time.time()

            # pause key
            if key == ord('p'):
                # pause audio
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()

                start_pause = time.time()
                # pause frame display until key pressed
                cv2.waitKey(-1)
                
            # resume paused audio   
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
                start_time += time.time() - start_pause # account for paused time

            # change fps if too fast/slow
            if frame_num % 100 != 0 :
                
                if end_time - start_time < 1 / 30.0 * frame_num:
                    
                    if prev_fps_incr:
                        fps_step = 5
                    else:
                        fps_step = fps_step / 2
                        
                    print("+ time is " + str(end_time - start_time) + " step is " + str(fps_step))
                    play_fps -= fps_step
                    prev_fps_incr = False

                elif end_time - start_time > 1 / 30.0 * frame_num:
                    
                    if not prev_fps_incr:
                        fps_step = 5
                    else:
                        fps_step = fps_step / 2

                    print("- time is " + str(end_time - start_time) + " step is " + str(fps_step))
                    play_fps += fps_step
                    prev_fps_incr = True

            frame_num += 1