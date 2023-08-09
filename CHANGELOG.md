# Covmatic RobotManager

## v0.0.6

- [server] Fixed bug happening when scheduler run in the middle of a check action operation.


## v0.0.5

## Fixed
- [calibrator] main *HOME* position can be saved directly.
- [calibrator] create *positions.json* file if not found.

## Added
- [setup] Setup module for creation of desktop link to start *robotmanager-server*

## v0.0.4

## Fixed
- [server] do not home when pick and drop plate are inside same machine

## Added
- [server] Robot operation has *aborted* state in case of error during pick
- [server] Abort drop operation if pick operation is aborted
- [server] Home the robot when errors occours during operations
- [server] Logs now are written to file also

## v0.0.3

### Fixed
- [server] After robot goes home after pick or drop the action request is marked as completed.
- [server] Pick-up is initiated only after drop request for the same plate is received.
- [server] After pick-up robot goes home
- [server] Now drop approach to slot with a linear movement
- [calibrator] Now after calibration robot is moved to home

## v0.0.2

- Added *waitress* as WSGI server


## v0.0.1

### Added
- Configuration parsed from file (see --help)