# RobotManager
Manager code for EVA robot from Automata.

## Warning
**This is a development program and not ready for production-use.
This is part of a project in development.**

## Table of Contents
* [Introduction](#introduction)
* [Installation](#installation)
* [Setup](#setup)
* [Calibration](#calibration)
* [Execution](#execution)
* [Testing](#testing)

## Introduction

The *covmatic-robotmanager* comes with two scripts callable in a command shell:
- *robotmanager-calibrator* is a helper program useful to save precise and repeatable calibrations.
- *robotmanager-server* is the main server that listen for actions to do;

Source code is on [ASST Bergamo Est repository](https://github.com/ASST-Bergamo-Est/covmatic-robotmanager)


## Installation

You can [install the Covmatic LocalWebServer via `pip`](https://pypi.org/project/covmatic-robotmanager):
```
<python> -m pip install covmatic-robotmanager
```
Where `<python>` should be changed for the Python instance you wish to install the Robotmanager onto. We will be following this convention for all the next instructions. 

## Setup
To set up the Robotmanager application, run
```
<python> -m covmatic_robotmanager.setup
``` 
This will create a desktop link and open in a text editor the file `.covmatic/robotmanager.conf` in your user home directory.
The configuration file should contain at least two parameter:
- *eva-ip*: this is the IP address of the Automata EVA robot;
- *eva-token*: this is the token used to authenticate with the EVA robot; create one token in the *Profile* Eva page.
Below an example of *robotmanager.conf* file:
```
eva-ip=192.168.1.1
eva-token=abcdefghijklmnrstuvwxyz
```

Please pay attention to any message regarding if the installed script are inside *PATH* directory; 
if you see these messages than you will not be able to start the *server* and the *calibrator* using the short commands
below, but instead you should locate the script installation directory to launch them.

## Calibration

Robotmanager-server uses pre-calibrated positions in order to know where to position the robot.

All the position are stored in a *.covmatic/positions.json* file in your home directory.

The data organization has these objects:
- a main **HOME** position which is the general home where the robot should stay waiting for operations and where it will return after each operation.
- a **target robot** intended as a machine or entity to reach (e.g. a pipetting robot)
- a **slot** intended as a part of a *target robot* to be reached (e.g. SLOT 1 of a pipetting robot)

The calibration flow should be as follows:

1. First of all launch the calibrator in a command line with:
   ```
   robotmanager-calibrator
   ```

2. Then calibrate the general *HOME* position:

   1. when asked for target insert *HOME*
   2. move manually the robot by pressing the *teach* button on the robot head
   3. when ready, press *Enter* and then ***s*** to save the position as home
   4. press _q_ to quit the program.

3. Calibrate the *HOME*, *DECK* and *HMAX* position for each target robot:
   For proper movement each *target robot* needs these point calibrated in order:
   1. **HOME** is the starting position that Eva will go to before entering the target robot.
         Eva should move freely between *HOME*s positions.
   2. **DECK** is a position where the gripper touches the deck of the target robot.
      This value is used to calculate heights of labware.
   3. **HMAX** is the maximum height reachable, calibrated with the Eva arm in the highest possibile position.
   
   To calibrate a position in a target robot you need to follow this sequence for each position:
   1. launch the *robotmanager-calibrator* script
   2. insert the *target robot* name (e.g. OT1)
   3. insert the *slot name* (e.g. HOME, DECK, HMAX, or anything used by protocols as SLOT1, SLOT2 etc.)
   4. follow the instruction of the calibrator (it will ask you to move the robot manually if the position is not found
   or to load a previously saved position)
   5. make any necessary adjustment with the keyboard (see the screen instructions)
   6. when ready you can test the saved position by pressing *w* and if necessary make any adjustment
   7. when the position is good press *s* to save and *q* to quit

After defining the three basic positions (HOME, DECK, HMAX) for a target robot you can define any other position for a target robot.
The Eva will use this data to calculate and execute a safe trajectory to pick up or drop off a plate.

## Execution

Covmatic Robotmanager server will listen for request from ***covmatic-robotstation*** package running on each target robot.
When a *pick* and *drop* or a *transfer* action are queued for a same plate name then the EVA robot will execute the plate transfer.

In case of error (e.g. plate not grabbed) every action related to that plate will be aborted.

## Testing

The Covmatic Robotmanager comes with a handful of tests to check that the code is doing as expected. 
It has been developed using a Test Driven Development approach.
To execute tests and coverage report just launch:
```
hatch run cov
```
