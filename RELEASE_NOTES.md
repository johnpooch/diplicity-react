# Release Notes

## Unreleased

### Accelerated Retreat/Adjustment Phases

In fixed-time games, retreat and adjustment phases can now resolve early when all eligible players confirm within a creator-set acceleration window. Movement phases are unaffected and always run their full cycle.

**Creating a game:** When creating a fixed-time game, the "Accelerated Retreat/Adjustment Phases" option appears on the Deadline tab. A slider lets the creator set the acceleration window (`W`); the "Minimum movement duration" readout shows the guaranteed floor (`movement_cycle − W`). The feature is enabled by default with a window of two frequency steps (e.g. 4 hours for daily games).

**In-game:** During a retreat or adjustment phase with acceleration enabled, the confirm button is active while the window is open and disabled (with a "Acceleration window closed" label) once it lapses. Movement phases keep the existing fixed-time behaviour (no confirm button).
