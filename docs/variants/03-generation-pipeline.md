# Generation Pipeline

**Status:** Placeholder - To Be Written

## Purpose

This document will specify the tooling that converts a validated Inkscape SVG into the three output formats required by the system: GoDip Go code, Django migrations, and React map JSON.

## Planned Contents

### 1. Pipeline Overview
- Input: Validated SVG file conforming to schema
- Outputs: GoDip, Django, React artifacts
- Error handling and reporting

### 2. SVG Parsing
- XML parsing approach
- Extracting province paths and metadata
- Handling coordinate transformations
- Calculating province centers from paths

### 3. GoDip Code Generation
- Generating `graph.New().Prov(...).Conn(...).Done()` chains
- Mapping province types to flags
- Generating `Units()` and `SupplyCenters()` maps
- Creating the complete `Variant` struct
- Output file structure

### 4. Django Migration Generation
- Generating Variant record migration
- Generating Nation records migration
- Generating Province records migration
- Generating template Phase migration
- Generating Unit and SupplyCenter migrations
- Migration dependency ordering

### 5. React JSON Generation
- Extracting SVG path `d` attributes
- Calculating center coordinates
- Positioning supply center indicators
- Extracting label positions and styling
- Generating backgroundElements, borders, impassableProvinces

### 6. Validation Pipeline
- Pre-generation validation (schema compliance)
- Post-generation validation (output integrity)
- Cross-output consistency checks

### 7. CLI Interface
- Command structure and arguments
- Configuration options
- Verbose/debug modes
- Dry-run capability

### 8. Implementation Considerations
- Language choice (Python recommended for SVG parsing + Django integration)
- Dependencies and packaging
- Testing strategy

## Dependencies

- Requires completion of: [01-variant-representations.md](./01-variant-representations.md), [02-svg-schema-design.md](./02-svg-schema-design.md)
- Informs: [04-variant-authoring-guide.md](./04-variant-authoring-guide.md)
