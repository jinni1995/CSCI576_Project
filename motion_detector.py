import cv2
import numpy as np

from timecode import FrameTimecode


class MotionDetector:
    def __init__(self, threshold, frames, kernel):
        self._threshold = threshold
        self._frames = frames
        self._kernel = kernel
        self._frames_processed = 0
        self.event_list = []
        self._video_fps = 30
        self._min_event_len = FrameTimecode(2, self._video_fps)
        self._pre_event_len = FrameTimecode("3.5s", self._video_fps)
        self._post_event_len = FrameTimecode("5s", self._video_fps)

    def _post_scan_motion(self):
        if not len(self.event_list) > 0:
            return

        if self.event_list:
            output_strs = [
                "-------------------------------------------------------------",
                "|   Event #    |  Start Time  |   Duration   |   End Time   |",
                "-------------------------------------------------------------"]
            output_strs += ["|  Event %4d  |  %s  |  %s  |  %s  |" % (
                event_num + 1, event_start.get_timecode(precision=3), event_duration.get_timecode(precision=3),
                event_end.get_timecode(precision=3)) for event_num, (event_start, event_end, event_duration) in
                            enumerate(self.event_list)]
            output_strs += [
                "-------------------------------------------------------------"]
            print("Scan-only mode specified, list of motion events:\n%s" + '\n'.join(output_strs))

            timecode_list = []
            for event_start, event_end, _ in self.event_list:
                timecode_list.append(event_start.get_timecode())
                timecode_list.append(event_end.get_timecode())
            print("[DVR-Scan] Comma-separated timecode values:\n%s" % (
                ','.join(timecode_list)))

    def scan_motion(self):
        bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
        event_window = []
        self.event_list = []
        num_frames_post_event = 0
        event_start = None
        curr_pos = FrameTimecode(0, self._video_fps)
        in_motion_event = False
        self._frames_processed = 0
        frame_nums_to_write = []

        scores = np.zeros(len(self._frames))
        ff = 0
        for frame_rgb in self._frames:
            # print(ff)
            frame_gray = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2GRAY)
            frame_mask = bg_subtractor.apply(frame_gray)
            if self._kernel is not None:
                frame_filt = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, self._kernel)
            else:
                frame_filt = frame_mask
            frame_score = np.sum(frame_filt) / float(frame_filt.shape[0] * frame_filt.shape[1])
            scores[ff] = frame_score
            ff += 1
            event_window.append(frame_score)
            event_window = event_window[-self._min_event_len.frame_num:]
            if in_motion_event:
                if frame_score >= self._threshold:
                    num_frames_post_event = 0
                else:
                    num_frames_post_event += 1
                    if num_frames_post_event >= self._post_event_len.frame_num:
                        in_motion_event = False
                        event_end = FrameTimecode(curr_pos.frame_num, self._video_fps)
                        event_duration = FrameTimecode(curr_pos.frame_num - event_start.frame_num, self._video_fps)
                        self.event_list.append((event_start, event_end, event_duration))
                        frame_nums_to_write.append((event_start.frame_num, event_end.frame_num))
            else:
                if len(event_window) >= self._min_event_len.frame_num and all(
                        score >= self._threshold for score in event_window):
                    in_motion_event = True
                    event_window = []
                    num_frames_post_event = 0
                    event_start = FrameTimecode(curr_pos.frame_num, self._video_fps)

            curr_pos.frame_num += 1
            self._frames_processed += 1

        if in_motion_event:
            curr_pos.frame_num -= 1
            event_end = FrameTimecode(curr_pos.frame_num, self._video_fps)
            event_duration = FrameTimecode(curr_pos.frame_num - event_start.frame_num, self._video_fps)
            self.event_list.append((event_start, event_end, event_duration))
            frame_nums_to_write.append((event_start.frame_num, event_end.frame_num))

        self._post_scan_motion()
        return self.event_list, frame_nums_to_write
