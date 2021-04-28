from collections import OrderedDict


class Shot:
    def __init__(self, num, start, end, motion_scores=None, audio_scores=None):
        # shot number
        self.num = num
        # frame number of start of shot
        self.start = start
        # frame number of end of shot (non-inclusive)
        self.end = end
        # dictionary of frame sequences and their individual motion scores in this format: {'0_1': 5.0, '1_2':5.0...}
        self.motion_scores = motion_scores
        # average motion score of the entire shot
        self.motion_score = None
        # average audio score of the entire shot
        self.audio_score = None
        # is a face detected in this shot?
        self.face_detected = False
        # score of the entire shot based on some combination of the motion/audio/other scores
        self.shot_score = None

    def get_shot_score(self):
        # TODO come up with a way of scoring the 3 metrics
        face_detection_bonus = 1.1 if self.face_detected else 1.
        # self.shot_score = (self.motion_score + self.audio_score) / 2 * face_detection_bonus
        self.shot_score = self.motion_score * self.audio_score * face_detection_bonus

    def get_motion_score(self):
        assert self.motion_scores is not None
        return sum(self.motion_scores.values()) / len(self.motion_scores.keys())

    def get_frames_with_highest_score(self):
        """
        Returns the start and end frame numbers of the highest scored frames in the shot
        :return:
        """
        assert self.shot_score is not None

        if self.shot_score == 0.:
            return None, None

        # if the shot is very short, it might not make sense and look abrupt
        if self.end - self.start < 45:
            return None, None

        # TODO we might want to tune this number later on. For now we use 300 frames, i.e. 10s is the maximum summarized shot length
        if self.end - self.start < 300:
            return self.start, self.end

        motion_scores_sorted = OrderedDict(sorted(self.motion_scores.items(), key=lambda item: item[1], reverse=True))
        frame_nums = set()
        for key, value in motion_scores_sorted.items():
            # TODO we have to tune this depending on how many frames are returned
            if frame_nums and max(frame_nums) - min(frame_nums) >= 270:
                break
            if value <= .3 * self.shot_score:
                break
            frame_nums.add(int(key.split('_')[0]))
            frame_nums.add(int(key.split('_')[1]))

        return min(frame_nums), max(frame_nums)
