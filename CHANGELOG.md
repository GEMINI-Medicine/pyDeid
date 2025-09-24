# Changelog

## `1.0.1`

- The _combine_overlapping_dates function in PHIPruner.py responsible for merging overlapping start-end key pair will now be run in a loop so it will no longer fail after running a single iteration.

## `1.0.0`

- Fix object oriented refactor so that accuracy and recall are like functional version
- Added multithreading capabilities to python function, cli, and pydeid builder through the `num_threads=<int>` parameter and the `set_multithreading` function respectively
- Fix partially overlapping date phis being replaced twice
- Fix entirely overlapping phis being replaced twice

## `0.1.0`

- Refactored `pyDeid` to an object oriented design.
