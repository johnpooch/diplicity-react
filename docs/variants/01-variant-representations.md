# Variant Representations Across System Components

This document describes how Diplomacy variants are represented across the three main components of the system: GoDip (Go adjudicator), the Django REST API service, and the React frontend. Understanding these representations is foundational for designing a system that allows community-created variants.

## Overview

A variant in Diplomacy defines:
- The map (provinces and their connections)
- The nations that can play
- Starting positions of units
- Supply center ownership
- Victory conditions

Each component of our system needs this information in a different format optimized for its purpose.

---

## 1. GoDip (Go Adjudicator)

**Repository:** `/Users/johnmcdowell/src/godip`
**Purpose:** Adjudicates orders and determines legal moves

### Core Data Structures

```go
// Variant definition (variants/common/common.go)
type Variant struct {
    Name        string
    Description string
    Rules       string
    CreatedBy   string
    Version     string
    Nations     []godip.Nation
    Graph       func() godip.Graph    // Province adjacency graph
    Start       func() (*state.State) // Starting game state
    // ... additional fields
}

// Graph node for provinces (graph/graph.go)
type Node struct {
    Name  godip.Province
    Subs  map[godip.Province]*SubNode  // Multi-coast support
    SC    *godip.Nation                // Supply center owner (nil if not SC)
}

type SubNode struct {
    Name         godip.Province
    Edges        map[godip.Province]*edge  // Adjacencies
    Flags        map[godip.Flag]bool       // Province type flags
}
```

### Province Type Flags

| Flag | Meaning | Unit Access |
|------|---------|-------------|
| `godip.Land` | Land province | Armies only |
| `godip.Sea` | Sea province | Fleets only |
| `godip.Coast...` | Coastal province (Land + Sea) | Both unit types |
| `godip.Convoyable` | Can participate in convoys | Used for convoy chains |

### Graph Building Pattern

GoDip uses a fluent builder pattern to define the province graph:

```go
// From variants/classical/start/map.go
func Graph() *graph.Graph {
    return graph.New().
        // Sea province (no supply center)
        Prov("nat").Conn("nrg", godip.Sea).Conn("cly", godip.Sea).
            Conn("lvp", godip.Sea).Conn("iri", godip.Sea).
            Conn("mid", godip.Sea).Flag(godip.Sea).

        // Coastal province with supply center
        Prov("lon").Conn("wal", godip.Coast...).Conn("yor", godip.Coast...).
            Conn("nth", godip.Sea).Conn("eng", godip.Sea).
            Flag(godip.Coast...).SC(godip.England).

        // Land province with supply center
        Prov("vie").Conn("tyr", godip.Land).Conn("boh", godip.Land).
            Conn("gal", godip.Land).Conn("bud", godip.Land).
            Conn("tri", godip.Land).
            Flag(godip.Land).SC(godip.Austria).

        Done()
}
```

**Builder Methods:**
- `Prov(name)` - Create or access a province
- `.Conn(target, ...flags)` - Create adjacency with movement constraints
- `.Flag(...flags)` - Set province type (Land, Sea, Coast)
- `.SC(nation)` - Mark as supply center owned by nation
- `.Done()` - Return the completed graph

### Multi-Coast Provinces

Some provinces have multiple coasts that fleets must distinguish between (e.g., Spain has North and South coasts):

```go
// Parent land province
Prov("spa").Conn("por", godip.Land).Conn("gas", godip.Land).
    Conn("mar", godip.Land).Flag(godip.Land).SC(godip.Neutral).

// North Coast (separate fleet route)
Prov("spa/nc").Conn("por", godip.Sea).Conn("mid", godip.Sea).
    Conn("gas", godip.Sea).Flag(godip.Sea).

// South Coast
Prov("spa/sc").Conn("mid", godip.Sea).Conn("por", godip.Sea).
    Conn("mar", godip.Sea).Conn("gol", godip.Sea).
    Conn("wes", godip.Sea).Flag(godip.Sea).
```

**Naming Convention:** `{province}/{coast}` where coast is typically `nc`, `sc`, `ec`, or `wc`.

### Starting Units

```go
// From variants/classical/start/units.go
func Units() map[godip.Province]godip.Unit {
    return map[godip.Province]godip.Unit{
        "edi":    {godip.Fleet, godip.England},
        "lvp":    {godip.Army, godip.England},
        "lon":    {godip.Fleet, godip.England},
        "bre":    {godip.Fleet, godip.France},
        "par":    {godip.Army, godip.France},
        "mar":    {godip.Army, godip.France},
        // ... all 22 starting units
        "stp/sc": {godip.Fleet, godip.Russia},  // Fleet on specific coast
    }
}
```

### Supply Centers

```go
// From variants/classical/start/supply_centers.go
func SupplyCenters() map[godip.Province]godip.Nation {
    return map[godip.Province]godip.Nation{
        "edi": godip.England,
        "lvp": godip.England,
        "lon": godip.England,
        "bre": godip.France,
        // ... all supply centers with their starting owners
        "bel": godip.Neutral,  // Neutral supply centers
        "hol": godip.Neutral,
    }
}
```

---

## 2. Django REST API Service

**Location:** `/service/`
**Purpose:** Stores game state, manages users, orchestrates adjudication

### Database Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `Variant` | Variant definition | `id`, `name`, `description`, `author`, `solo_victory_sc_count` |
| `Nation` | Playable nations | `name`, `color`, `variant` (FK) |
| `Province` | Map provinces | `province_id`, `name`, `type`, `supply_center`, `parent`, `variant` (FK) |
| `Phase` | Game state snapshot | `variant` (FK), `season`, `year`, `type`, `status` |
| `Unit` | Unit positions | `type`, `nation` (FK), `province` (FK), `phase` (FK) |
| `SupplyCenter` | SC ownership | `nation` (FK), `province` (FK), `phase` (FK) |

### Province Types

| Type | Description |
|------|-------------|
| `"land"` | Armies only |
| `"sea"` | Fleets only |
| `"coastal"` | Both unit types |
| `"named_coast"` | Sub-province for multi-coast provinces (has `parent` FK) |

### Data Population via Migrations

Variants are populated through Django migrations in dependency order:

```
1. variant/migrations/0002_add_classical_variant.py     → Variant record
2. nation/migrations/0002_add_classical_nations.py      → Nation records
3. province/migrations/0002_add_classical_provinces.py  → Province records
4. phase/migrations/0002_add_classical_template_phase.py → Template Phase
5. unit/migrations/0002_add_classical_units.py          → Starting Units
```

### Template Phase Pattern

Each variant has a "template" phase (`status="template"`, `game=None`) that stores starting positions. When a game is created, this template is cloned:

```python
Phase.objects.create(
    game=None,           # null indicates template
    variant=variant,
    status="template",
    season="Spring",
    year=1901,
    type="Movement",
)
```

### API Response Format

```json
{
    "id": "classical",
    "name": "Classical",
    "description": "The original game of Diplomacy",
    "author": "Allan B. Calhamer",
    "solo_victory_sc_count": 18,
    "nations": [
        {"name": "England", "color": "#2196F3"},
        {"name": "France", "color": "#80DEEA"}
    ],
    "provinces": [
        {
            "id": "lon",
            "name": "London",
            "type": "coastal",
            "supply_center": true,
            "parent_id": null,
            "named_coast_ids": []
        },
        {
            "id": "stp/nc",
            "name": "St. Petersburg (NC)",
            "type": "named_coast",
            "supply_center": false,
            "parent_id": "stp",
            "named_coast_ids": []
        }
    ],
    "template_phase": {
        "units": [
            {"type": "Fleet", "nation": {"name": "England"}, "province": {"id": "lon"}}
        ],
        "supply_centers": [
            {"nation": {"name": "England"}, "province": {"id": "lon"}}
        ]
    }
}
```

### GoDip Communication Format

The service communicates with GoDip via HTTP, sending phase state as JSON:

```json
{
    "Season": "Spring",
    "Year": 1901,
    "Type": "Movement",
    "Units": {
        "edi": {"Type": "Fleet", "Nation": "England"},
        "lvp": {"Type": "Army", "Nation": "England"}
    },
    "SupplyCenters": {
        "lon": "England",
        "par": "France"
    },
    "Orders": {
        "England": {
            "edi": ["Move", "nor"]
        }
    }
}
```

---

## 3. React Frontend

**Location:** `/packages/web/`
**Purpose:** Renders interactive map and game UI

### Map Data Location

Map JSON files are stored at `/packages/web/public/maps/{variantId}.json`

### Map JSON Structure

```typescript
type MapData = {
    width: number;       // SVG canvas width
    height: number;      // SVG canvas height

    provinces: Array<{
        id: string;      // 3-letter province code (e.g., "lon")

        path: {
            d: string;   // SVG path definition
            styles: {
                fill: string;
                stroke: string;
                strokeWidth: string;
                fillOpacity: string;
            }
        };

        center: {        // Position for rendering units/orders
            x: number;
            y: number;
        };

        supplyCenter?: { // Position for SC indicator (if applicable)
            x: number;
            y: number;
        };

        text?: Array<{   // Province name labels
            id: string;
            value: string;       // Human-readable name
            point: { x: number; y: number };
            styles: {
                fontSize: string;
                fontFamily: string;
                fontWeight: string;
                fill: string;
            };
            transform?: string;  // e.g., "rotate(1)"
        }>;
    }>;

    backgroundElements: Array<{  // Water/terrain fills
        id: string;
        d: string;
        styles: { fill: string; stroke: string; }
    }>;

    borders: Array<{             // Province boundary lines
        id: string;
        d: string;
    }>;

    impassableProvinces: Array<{ // Non-playable areas
        id: string;
        d: string;
    }>;
};
```

### Key Insight: Separation of Concerns

The map JSON contains **only visual/geometric data**:
- SVG paths for province shapes
- Coordinates for unit/order rendering
- Supply center indicator positions
- Province labels and styling

Province **type and adjacency information** comes from the Django API's `Variant.provinces` response. The React app combines both sources to render the complete interactive map.

### Existing Maps

| Variant | File | Provinces | Dimensions |
|---------|------|-----------|------------|
| Classical | `classical.json` | 81 | 1524 × 1357 |
| Hundred | `hundred.json` | 45 | 662 × 1082 |

### Map Loading

```typescript
// hooks/useMapData.ts
const fetchMapData = async (variantId: string): Promise<MapData> => {
    const response = await fetch(`/maps/${variantId}.json`);
    if (!response.ok) {
        // Falls back to classical if variant map doesn't exist
        return fetch("/maps/classical.json").then(r => r.json());
    }
    return response.json();
};
```

---

## 4. Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VARIANT DATA FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐                                                    │
│  │ Source SVG  │ (proposed future input)                            │
│  │ (Inkscape)  │                                                    │
│  └──────┬──────┘                                                    │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    GENERATION PIPELINE                       │    │
│  │                    (future tooling)                          │    │
│  └──────┬─────────────────┬─────────────────┬──────────────────┘    │
│         │                 │                 │                        │
│         ▼                 ▼                 ▼                        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                │
│  │   GoDip     │   │   Django    │   │   React     │                │
│  │   (Go)      │   │  (Python)   │   │   (JSON)    │                │
│  ├─────────────┤   ├─────────────┤   ├─────────────┤                │
│  │ • Graph     │   │ • Variant   │   │ • SVG paths │                │
│  │   nodes     │   │   model     │   │ • Centers   │                │
│  │ • Adjacency │   │ • Nations   │   │ • Labels    │                │
│  │ • Flags     │   │ • Provinces │   │ • Styling   │                │
│  │ • SCs       │   │ • Template  │   │             │                │
│  │ • Units     │   │   Phase     │   │             │                │
│  └─────────────┘   └─────────────┘   └─────────────┘                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Requirements Matrix

For a single source (e.g., an Inkscape SVG) to generate all three representations, it must encode:

| Data Element | GoDip | Django | React | Source Encoding |
|--------------|-------|--------|-------|-----------------|
| Province ID | Required | Required | Required | `id` attribute |
| Province Name | Optional | Required | Required | `data-name` attribute |
| Province Type | Required (flags) | Required | Derived from API | `data-type` attribute |
| Adjacencies | Required (graph) | Not stored | Not needed | `data-adjacent` or geometric |
| Supply Center | Required | Required | Visual position | `data-supply-center` |
| Home Nation | Required | Required | Not needed | `data-home` attribute |
| Starting Units | Required | Required | Not needed | `data-starting-unit` |
| Visual Shape | Not needed | Not needed | Required | SVG `d` path |
| Center Point | Not needed | Not needed | Required | `data-center` or calculated |
| Multi-Coast Parent | Required | Required (FK) | Not needed | `data-parent` attribute |

---

## 6. Next Steps

This document establishes the foundation for designing a community variant authoring system. Future documents will cover:

1. **02-svg-schema-design.md** - Detailed specification for the Inkscape SVG format
2. **03-generation-pipeline.md** - Tools to convert SVG → GoDip/Django/React formats
3. **04-variant-authoring-guide.md** - User-facing tutorial for creating variants in Inkscape
