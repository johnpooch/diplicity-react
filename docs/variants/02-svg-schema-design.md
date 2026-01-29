# SVG Schema Design

**Status:** Placeholder - To Be Written

## Purpose

This document will define the exact specification for Inkscape SVG files used to create Diplomacy variants. It will serve as the authoritative reference for variant authors.

## Planned Contents

### 1. SVG Structure Requirements
- Required layers and groups
- Naming conventions for elements
- Coordinate system and dimensions

### 2. Province Element Specification
- Required `id` format (3-letter codes)
- Path requirements for province shapes
- Required `data-*` attributes:
  - `data-name` - Human-readable province name
  - `data-type` - Province type (land, sea, coastal)
  - `data-supply-center` - Whether province has a supply center
  - `data-home` - Home nation (if supply center)
  - `data-adjacent` - Comma-separated list of adjacent provinces
  - `data-starting-unit` - Starting unit type and nation (if applicable)

### 3. Multi-Coast Province Handling
- Parent province definition
- Coast sub-province naming (`{id}/nc`, `{id}/sc`, etc.)
- Coast-specific adjacencies

### 4. Nation Definition
- How nations are declared
- Color assignments
- Starting unit assignments

### 5. Visual Elements
- Background/water layers
- Border styling
- Label positioning
- Impassable area marking

### 6. Validation Rules
- Required elements checklist
- Adjacency consistency checks
- Supply center and unit validation

### 7. Example SVG
- Complete annotated example of a simple variant
- Snippets showing each element type

## Dependencies

- Requires completion of: [01-variant-representations.md](./01-variant-representations.md)
- Informs: [03-generation-pipeline.md](./03-generation-pipeline.md), [04-variant-authoring-guide.md](./04-variant-authoring-guide.md)
