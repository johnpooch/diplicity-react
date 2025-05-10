# Adjudicator

## Overview

The service uses the `godip` adjudicator service to adjudicate each phase.

Adjudication takes place when all members of a game have confirmed there orders
(excluding users who have been eliminated or kicked) **or** when the phase
duration elapses.

## Implementation

When a new phase is created, a task is added to the task queue to adjudicate the
phase after the phase duration.

The adjudication process is as follows:

- The task queue receives the task to adjudicate the phase.
- The task queue retrieves all entities from the database whic required to
  construct a request to `godip` to adjudicate the phase.
- The task queue constructs the request to `godip` to adjudicate the phase.
- The task queue sends the request to `godip` to adjudicate the phase.
- The task queue receives the response from `godip` and updates the database with
  the results of the adjudication.

The request to `godip` is a POST request with a JSON body which is defined in
`../godip-open-api.json`.
