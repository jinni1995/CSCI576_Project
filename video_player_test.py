from video_player import VideoPlayer

# if __name__ == "__main__":

video_input = 'input/project_dataset/frames/concert'
audio_samples = 'input/project_dataset/audio/concert.wav'

player = VideoPlayer(video_input, audio_samples, 30)
player.play()