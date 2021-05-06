# CSCI 576 Final Project

This is the final project for CSCI 576.

## Authors

Jing Nee Ng
Zhengxie Hu
Cameron Podd

## Installation

To install this project, complete the following steps. These steps assume Python 3
is already installed on your system.

1.  Download the inputs from the CSCI 576 DEN website. Unzip these into the `input` folder.
    The input folder should have a `project_dataset` folder within it.

2.  Create a new Python 3 virtual environment. On MacOS and Linux, the command for that is this:
    `python3 -m venv venv`

3.  Activate the virtual environment. On MacOS, the command is this:
    `source ./venv/bin/activate`. On Linux, the command is: `. venv/bin/activate`

Note - to deactivate, simply type `deativate`

4.  Install the required python modules with the command `pip3 install -r requirements.txt`.

5.  Install the required dependencies that cannot be installed with pip. These requirements
    can be found in the file `non-pip-requirements.txt`. Installing these will vary depending
    on your system. With MacOS, the best way to install these is through HomeBrew. To do so,
    run `cat non-pip-requirements | xargs brew install`. However, this will definitely change
    depending on your system! For Linux, run `sudo apt-get install` or `sudo pacman -S` or 
    `sudo yum install`, depending on your distribution.
    

## Running

To run this project, ensure that `main.py` is executable. On MacOS and Linux, this is
done by running `chmod +x main.py`.

Next, create an `ouput` folder. On MacOS and Linux, this is done by running `mkdir output`.

After that, simply run the `main.py` script. On MacOS, this is done by running `./main.py`. On Linux, run `python3 main.py`.

## Shot Boundary Detection

We
used [PySceneDetect's ContentDetector](https://pyscenedetect.readthedocs.io/en/latest/reference/detection-methods/#content-aware-detector)
to segment out each shot. The content-aware algorithm uses the HSV color space to measure the delta between frames. If
the difference exceeds a pre-defined threshold value, then the two frames belong to different scenes.

## Shot Scoring Metrics

We used 3 different metrics to score each shot (in order of importance): motion, audio, and face detection.

### Motion

We used the [blockmatching](https://github.com/duducosmos/blockmatching) library to track the amount of motion across
frames with optical flow. We first resize the video frames to half its original size (160x90) to optimize program run
time. We also extract the foreground and use that to apply the optical flow
algorithm ([more details here](https://ieeexplore.ieee.org/document/5680866)). Since motion may arise from the movement
of the foreground object, the movement of the camera, or the joint movement of the two, this technique works out well.

As we iterate through the frames, the library divides every 2 frames (previous and current) into blocks. For each block,
we attempt to find the best matching block in the previous frame (based on sum of absolute difference). Based on these "mappings", the library would return an array of displacement vectors for the blocks. We sum up the Euclidean distances
and get the average, using that as the ***shot's motion score***. We also keep track of each frame's individual motion score.

### Audio

For audio scoring, we simply take the amplitudes of the samples corresponding to the particular shot and take an
average. Once we calculate this for all shots, we normalize the scores.

### Face Detection

We used the [face_recognition](https://github.com/ageitgey/face_recognition) library to detect and locate faces in each
shot.

## Frame Selection

The scores are combined using this formula: `motion_score * audio_score * face_detection_bonus`
where `face_detection_bonus` is 1.1 if faces are detected in the shot, and 1.0 otherwise. We then sort the shots based
on descending scores. We also introduced two criteria to select the frames from each shot.

1. A shot must have a minimum of 45 frames. Before introducing this criteria, we noticed that some shot changes are very
   abrupt. In addition, when the number of frames are low, the audience may not have time to react to the content. This
   ensures a smoother video.
2. If a shot has more than 300 frames (10 seconds), it may be too long and we could miss the selection of other shots
   that may be just as interesting. Hence, we keep track of the motion scores between frames of each shot. We sort this
   in descending order and as long as the score is in the top 70%, we will insert the frame numbers in a set. The
   selected frames begin and end from the min and max of the set.

Of course, once we have at least a minimum of 85 seconds of video, we will stop selecting frames.

## Conclusion

Our scoring metrics and frame selection criteria are producing videos that are smooth across different genres. In
addition, our program only takes about **5 mins** to complete the video evaluation. Here's a speed up GIF of the GUI in
action:
![GUI Preview](gui_preview.gif)
