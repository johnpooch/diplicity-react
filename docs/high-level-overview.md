# Diplicity React: iOS Capacitor Integration — High-Level Overview

## Background

Diplicity React is a React Vite TypeScript web app that communicates with a Django REST API backend using a Google Auth flow. The goal of this milestone is to produce a native iOS app using Capacitor JS, submitted to the App Store.

A significant branch implementing this work was lost due to a machine wipe. Rather than simply rebuilding the lost work, this is an opportunity to establish a more robust, automated development workflow that will make the implementation faster, higher quality, and resilient to future disruption.

---

## The Broad Plan

The work is divided into two major phases.

### Phase 1: Orchestrator Workflow Setup

Before any implementation work begins, we will invest in building an automated development workflow powered by Claude Code custom commands and a GitHub-based state machine. This workflow will:

- Automatically scope and enrich GitHub issues using codebase investigation
- Apply staff engineer review to both issues and pull requests, calibrated to our engineering philosophy
- Implement issues in isolated git worktrees and raise pull requests
- Enforce human review at every critical decision point
- Learn from human feedback and continuously improve its own review quality
- Orchestrate all of the above across parallel Claude Code agents, respecting the dependency graph between issues

This investment will pay off quickly given the size of the Capacitor iOS milestone. It also produces reusable infrastructure that will accelerate all future development on this project.

### Phase 2: Capacitor iOS Implementation

Once the workflow is validated on a dummy repository, we will apply it to the real Capacitor iOS work. This involves:

1. Scoping all sub-issues for the milestone fully before any implementation begins, surfacing all external dependencies (credentials, tokens, Apple Developer configuration) so they can be resolved as a batch
2. Resolving all prerequisites
3. Implementing the work in parallel across Claude Code agents, respecting the dependency graph between issues, with human review at each pull request

---

## Key Principles

**Human in the loop at every critical moment.** The orchestrator pauses and waits for explicit human approval before issues are implemented and before pull requests are merged. Agents do not advance past these gates autonomously.

**Issues as the source of truth.** All planning, context, and progress state lives in GitHub issues. This means the work is resilient to machine loss and provides a full audit trail.

**Quality encoded in the workflow.** The staff engineer review commands are calibrated to our actual engineering philosophy — simplicity, no premature optimisation, clean testable code — rather than generic best practices. Human feedback continuously improves this calibration.

**Prerequisites resolved before implementation.** All external dependencies (API keys, Apple credentials, Firebase config) are identified during the scoping phase and resolved before any implementation agent is launched.

**Parallelism where safe.** The dependency graph between issues is explicit and respected. Where issues are independent, parallel Claude Code agents handle them simultaneously.
