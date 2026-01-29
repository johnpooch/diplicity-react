# Variant Authoring Guide

**Status:** Placeholder - To Be Written

## Purpose

This document will be a user-facing tutorial that walks non-technical users through the complete process of creating a custom Diplomacy variant using Inkscape. It is intended to be the basis for a YouTube tutorial video.

## Planned Contents

### 1. Introduction
- What is a variant?
- What you'll create by the end of this guide
- Prerequisites (Inkscape installation, basic familiarity)

### 2. Setting Up Your Workspace
- Installing Inkscape
- Downloading the variant template
- Understanding the layer structure

### 3. Drawing Your Map
- Creating province shapes
- Tips for clean, non-overlapping paths
- Styling land vs. sea vs. coastal provinces
- Adding impassable areas (Switzerland, etc.)

### 4. Adding Province Metadata
- Using Inkscape's XML Editor
- Setting province IDs (3-letter codes)
- Adding `data-name` for display names
- Setting `data-type` (land, sea, coastal)

### 5. Defining Adjacencies
- Understanding adjacency in Diplomacy
- Adding `data-adjacent` attributes
- Handling special cases (canals, multi-coast)

### 6. Configuring Supply Centers
- Marking supply centers with `data-supply-center`
- Assigning home nations with `data-home`
- Positioning SC indicators

### 7. Setting Up Nations
- Defining the nations for your variant
- Assigning nation colors
- Balancing starting positions

### 8. Placing Starting Units
- Adding `data-starting-unit` attributes
- Army vs. Fleet placement rules
- Multi-coast fleet placement

### 9. Adding Labels and Styling
- Province name labels
- Positioning and rotating text
- Background and border styling

### 10. Validating Your Variant
- Running the validation tool
- Common errors and how to fix them
- Checklist before generation

### 11. Generating Output Files
- Running the generation pipeline
- Understanding the output files
- Testing your variant locally

### 12. Submitting Your Variant
- Packaging for submission
- Community review process
- Getting your variant added to the game

### Appendices
- A. Complete attribute reference
- B. Troubleshooting common issues
- C. Example variants to study

## Dependencies

- Requires completion of: [02-svg-schema-design.md](./02-svg-schema-design.md), [03-generation-pipeline.md](./03-generation-pipeline.md)
