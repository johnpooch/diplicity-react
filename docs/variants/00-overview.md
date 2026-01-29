# Community-Created Variants: Feature Overview

## Vision

Enable non-technical users to create custom Diplomacy variants using Inkscape (a free, open-source vector graphics editor). A single SVG file, following a defined schema, becomes the source of truth from which all system components are automatically generated.

## Problem Statement

Currently, creating a new Diplomacy variant requires:

1. **GoDip (Go)** - Writing Go code to define the province graph, adjacencies, flags, supply centers, and starting units
2. **Django Service** - Creating database migrations to populate Variant, Nation, Province, Phase, and Unit records
3. **React Frontend** - Creating a JSON file with SVG paths, center coordinates, and label positions

This multi-step process requires programming knowledge across three languages (Go, Python, TypeScript/JSON) and understanding of each system's data model. It's inaccessible to the broader Diplomacy community.

## Proposed Solution

**Single Source of Truth:** An Inkscape SVG file that encodes both visual and logical information through:
- SVG paths for province shapes (visual)
- `data-*` attributes for metadata (logical): province type, adjacencies, supply centers, home nations, starting units

**Automated Generation Pipeline:** Tooling that parses the SVG and generates:
- GoDip variant code (Go)
- Django migration files (Python)
- React map JSON (JSON)

**User-Friendly Workflow:**
1. User draws map in Inkscape
2. User adds metadata via Inkscape's XML editor or a custom extension
3. User runs generation tool
4. Generated files are ready for deployment

## Success Criteria

- A non-programmer can create a working variant by following a YouTube tutorial
- The SVG schema is simple enough to validate manually
- Generated code requires no manual editing
- Existing variants (Classical, Hundred, Italy vs Germany) can be recreated from SVG sources

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      VARIANT AUTHORING                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Inkscape SVG                          │   │
│  │  • Province shapes (paths)                               │   │
│  │  • Metadata (data-* attributes)                          │   │
│  │  • Labels and styling                                    │   │
│  └─────────────────────┬───────────────────────────────────┘   │
│                        │                                        │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               Generation Pipeline                        │   │
│  │  • Parse SVG                                             │   │
│  │  • Validate schema                                       │   │
│  │  • Generate outputs                                      │   │
│  └────────┬─────────────────┬─────────────────┬────────────┘   │
│           │                 │                 │                 │
│           ▼                 ▼                 ▼                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   GoDip     │   │   Django    │   │   React     │           │
│  │   (Go)      │   │  (Python)   │   │   (JSON)    │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Documentation Roadmap

| Document | Purpose |
|----------|---------|
| [00-overview.md](./00-overview.md) | This document - high-level feature vision |
| [01-variant-representations.md](./01-variant-representations.md) | How variants are represented in each system component |
| [02-svg-schema-design.md](./02-svg-schema-design.md) | Specification for the Inkscape SVG format |
| [03-generation-pipeline.md](./03-generation-pipeline.md) | Tools to convert SVG to GoDip/Django/React formats |
| [04-variant-authoring-guide.md](./04-variant-authoring-guide.md) | User-facing tutorial for creating variants |

## Key Decisions (To Be Made)

1. **Adjacency Encoding**: Explicit `data-adjacent` attributes vs. geometric detection from shared borders?
2. **Tooling Language**: Python script, Node.js CLI, or web-based tool?
3. **Validation**: How strict should schema validation be? What errors are recoverable?
4. **Distribution**: How are community variants shared and installed?

## Related Resources

- **GoDip Repository**: Contains the Go adjudicator and existing variant definitions
- **Django Service**: `/service/` - REST API and database models
- **React Frontend**: `/packages/web/` - Interactive map component and existing map JSON files
