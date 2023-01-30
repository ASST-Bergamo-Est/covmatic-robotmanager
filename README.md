# RobotManager
Manager code for EVA robot from Automata.

## Warning
**This is a development program and not ready for production-use.
This is part of a project in development.**

## Use

The *covmatic-robotmanager* comes with two scripts callable in a command shell:
- *robotmanager-calibrator* is a helper program useful to save precise and repeatable calibrations.
- *robotmanager-server* is the main server that listen for actions to do;

## Data organization

The data organization has these objects:
- a **target robot** intended as a machine or entity made of reachable points;
- a **slot** intended as a part of a * target robot* to be reached.

For proper movement each *target robot* needs these point calibrated in order:
1. **HOME** is the starting position that Eva will go to before entering the target robot.
   Eva should move freely between *HOME*s positions.
2. **DECK** is a position where the gripper touches the deck of the target robot.
   This value is used to calculate heights of labware.
3. **HMAX** is the maximum height reachable, calibrated with the Eva arm in the highest possibile position.

After defining these three basic positions you can define any other position for a target robot.
The Eva will use this data to calculate and execute a safe trajectory to pick up or drop off a plate.

## Calibration
Calibrations are saved using the *robotmanager-calibrator* program.
Positions data are saved in the user home folder.

