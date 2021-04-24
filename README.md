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
