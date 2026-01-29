# Variant Creator App - Technical Design Document

## Overview

The Variant Creator is a standalone web application that enables non-technical users to create custom Diplomacy variants. Users draw maps in Inkscape, then use this wizard-based tool to add game metadata (province types, adjacencies, starting positions, etc.) through a guided visual interface.

### Goals

- Enable variant creation without programming knowledge
- Complete a variant in under 90 minutes (after SVG is drawn)
- Produce a self-contained JSON file that can be submitted for review
- Support resumable editing (upload JSON to continue)

---

## Architecture

### Separate Application

The Variant Creator exists as a separate React application within the `diplicity-react` monorepo, but is built and deployed independently from the main web app.

```
diplicity-react/
├── packages/
│   ├── web/                    # Existing game app
│   └── variant-creator/        # New variant creator app
├── service/                    # Django backend (not used by variant-creator)
└── docs/
```

### Fully Client-Side

The app runs entirely in the browser with no backend:
- SVG parsing happens client-side
- State is stored in memory and localStorage
- Output is a downloadable JSON file
- No authentication required

---

## Tech Stack

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Framework | React + TypeScript | Consistent with main app |
| Build | Vite | Fast, simple |
| Styling | Tailwind + shadcn/ui | Consistent with main app |
| State | JSON blob in useState + localStorage | Simple, JSON is source of truth |
| SVG Geometry | Paper.js (headless mode) | Excellent path operations for adjacency detection |
| SVG Rendering | Native SVG + React | Interactive overlays, no canvas conversion |
| Drag/Drop | @dnd-kit or pointer events | Position adjustments |
| File Handling | Native File API | Upload SVG/JSON, download JSON |
| Deployment | Netlify | Simple static hosting |

---

## Data Structures

### VariantDefinition (Output JSON)

```typescript
interface VariantDefinition {
  // Metadata
  name: string;
  description: string;
  author: string;
  version: string;
  soloVictorySCCount: number;

  // Nations
  nations: Nation[];

  // Provinces (includes extracted SVG paths)
  provinces: Province[];

  // Named coasts for multi-coast provinces
  namedCoasts: NamedCoast[];

  // Visual elements preserved from SVG
  decorativeElements: DecorativeElement[];

  // Canvas dimensions
  dimensions: { width: number; height: number };
}

// Note: Phase navigation is controlled via URL routing (e.g., /phase/0, /phase/1)
// rather than storing wizard state in the JSON. This keeps the JSON focused on
// variant data and allows bookmarkable URLs for each phase.

interface Nation {
  id: string;                    // "england"
  name: string;                  // "England"
  color: string;                 // "#2196F3"
}

interface Province {
  id: string;                    // "ber"
  name: string;                  // "Berlin"
  type: "land" | "sea" | "coastal" | "namedCoasts";
  path: string;                  // SVG path d attribute
  homeNation: string | null;     // "germany" or null for neutral
  supplyCenter: boolean;
  startingUnit: {
    type: "Army" | "Fleet";
  } | null;                      // Nation inferred from homeNation
  adjacencies: string[];         // ["mun", "pru", "sil", "kie"]

  // Multiple text elements can be associated (e.g., "Spain" + "NC")
  labels: Label[];

  // Position data for rendering game elements
  unitPosition: { x: number; y: number };
  dislodgedUnitPosition: { x: number; y: number };
  supplyCenterPosition?: { x: number; y: number }; // Only for SC provinces
}

interface Label {
  text: string;
  position: { x: number; y: number };
  rotation?: number;             // Rotation angle in degrees
  source: "svg" | "generated";
  styles?: {
    fontSize?: string;
    fontFamily?: string;
    fontWeight?: string;
    fill?: string;
  };
}

// Named coasts are kept separate from Province because they have different behavior:
// - No supply centers (SCs belong to parent province)
// - Different adjacency rules (fleets use coast adjacencies, armies use parent's)
// - Only exist for fleet positioning purposes
interface NamedCoast {
  id: string;                    // "stp/nc"
  name: string;                  // "St. Petersburg (North Coast)"
  parentId: string;              // "stp"
  path: string;                  // SVG path d attribute
  adjacencies: string[];         // Different from parent's adjacencies
  unitPosition: { x: number; y: number };
  dislodgedUnitPosition: { x: number; y: number };
}

interface DecorativeElement {
  id: string;
  type: "path" | "text" | "group";
  content: string;               // SVG markup or path d
  styles?: Record<string, string>;
}
```

---

## SVG Input Requirements

### Required Layers

| Layer Name | Contents | Required |
|------------|----------|----------|
| `provinces` | Province paths (closed shapes) | Yes |
| `named-coasts` | Coast sub-paths for multi-coast provinces | No |
| `text` | Province labels and other text | No |

### Optional Layers

All other layers (background, borders, decorative elements) are preserved as `decorativeElements` in the output.

### Province Path Requirements

- Must be closed paths (start and end points connected)
- Should have unique element IDs (for SVG re-upload matching)
- Recommended: Set element ID to province ID in Inkscape (Object Properties)

### Example SVG Structure

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1524 1357">
  <!-- Background layer - preserved as decorative -->
  <g inkscape:label="background">
    <path d="M0,0 L1524,0 L1524,1357 L0,1357 Z" fill="#8BA5D0"/>
  </g>

  <!-- Provinces layer - extracted for wizard -->
  <g inkscape:label="provinces">
    <path id="ber" d="M734,456 L789,423 L812,478..." fill="#C8B896"/>
    <path id="mun" d="M698,534 L734,456 L789,512..." fill="#C8B896"/>
  </g>

  <!-- Named coasts layer - extracted for multi-coast provinces -->
  <g inkscape:label="named-coasts">
    <path id="stp-nc" d="M1100,200 L1150,180..." fill="none" stroke="#333"/>
    <path id="stp-sc" d="M1080,280 L1120,300..." fill="none" stroke="#333"/>
  </g>

  <!-- Text layer - associated with provinces in wizard -->
  <g inkscape:label="text">
    <text x="760" y="470">Berlin</text>
    <text x="720" y="560">Munich</text>
  </g>

  <!-- Borders layer - preserved as decorative -->
  <g inkscape:label="borders">
    <path d="M734,456 L789,423..." fill="none" stroke="#333"/>
  </g>
</svg>
```

---

## Wizard Phases

### Phase 0: Variant Setup

**Purpose:** Define variant metadata and nations.

**Inputs:**
- Variant name, description, author
- Nation definitions (name + color for each)
- Solo victory supply center count

**UI:**
- Form with text inputs
- Dynamic nation list with color pickers
- "Add Nation" / "Remove Nation" buttons

**Validation:**
- At least 2 nations required
- Unique nation names
- Victory SC count > 0

---

### Phase 1: Province Details

**Purpose:** Define metadata for each province.

**Inputs (per province):**
- ID (3-letter code, auto-suggested from name)
- Name (full display name)
- Type (land / sea / coastal / namedCoasts)
- Home nation (dropdown, or "None")
- Supply center (toggle)
- Starting unit (Army/Fleet/None + nation)

**UI:**
- Spreadsheet/table view with all provinces
- Hover over row → highlight province on map (temporary)
- Click row → select province (persistent highlight)
- Tab through fields for fast entry
- Bulk selection for common operations
- When type is "namedCoasts": show sub-panel to associate coast paths from `named-coasts` layer

**Auto-Suggestions:**
- ID derived from name: "Berlin" → "ber", "North Sea" → "nth"
- Default type: "land"
- Default: no supply center, no starting unit

**Validation:**
- Unique province IDs
- IDs must be 3 lowercase letters
- Fleet cannot start on land-only province
- Army cannot start on sea province
- Starting units can only exist on home supply centers (nation inferred from homeNation)

**Coast Association (for "namedCoasts" type):**
- When user selects "namedCoasts" type, show coast paths from `named-coasts` layer
- User clicks coast paths on map to associate with current province
- Associated coasts displayed in the province row
- Each coast path can only be associated with one parent province

---

### Phase 2: Text Association

**Purpose:** Link SVG text elements to provinces for interactive highlighting.

**Inputs:**
- For each text element from SVG "text" layer:
  - Associated province (dropdown) or "None" (decorative)

**UI:**
- Map shows all text elements
- Table lists text elements with province dropdown
- Click text on map to select in table
- Click province on map to associate with selected text

**Auto-Detection:**
- Calculate proximity of each text element to province centroids
- Pre-populate associations for user to confirm

**Behavior:**
- Multiple text elements can associate with same province ("Spain" + "NC")
- Text with "None" association preserved as decorative
- Provinces without associated text will get generated labels in Phase 4

---

### Phase 3: Adjacencies

**Purpose:** Define which provinces connect to each other.

**Inputs:**
- For each province: list of adjacent province IDs

**UI:**
- Current province highlighted on map
- Adjacent provinces shown as selected (toggleable)
- Click any province to add/remove adjacency
- "Next" / "Previous" buttons to navigate provinces
- Progress indicator (e.g., "Province 34 of 81")

**Auto-Detection:**
- Use Paper.js to detect path intersections
- Paths that share border points are adjacent
- Pre-populate adjacencies for user to confirm

**Validation:**
- Adjacencies must be bidirectional (enforced automatically)
- Each province should have at least 1 adjacency
- Warning for isolated provinces

---

### Phase 4: Visual Editor

**Purpose:** Adjust all positions and edit generated labels.

**All Elements Shown:**
- Unit markers (at calculated positions)
- Dislodged unit markers (offset from unit positions)
- Supply center markers (for SC provinces)
- Labels (from SVG associations + generated for remaining)

**Interactions:**
- Click any element to select
- Drag to reposition
- Double-click label to edit text
- Rotate labels using rotation handle or input field (degrees)
- Toggle visibility by element type
- "Reset to Auto" button per element
- "Accept All" to complete phase

**UI:**
- Map canvas with all markers visible
- Toggles: Show Units / Dislodged / Supply Centers / Labels
- Selected element panel showing coordinates and edit options

**Auto-Positioning:**
- Unit: Province centroid
- Dislodged unit: Offset from centroid (e.g., +10px, +10px)
- Supply center: Offset from centroid (e.g., -15px, -15px)
- Generated labels: Province centroid

---

### Phase 5: Review & Export

**Purpose:** Final validation and JSON download.

**Display:**
- Summary statistics (province count, SC count, nation breakdown)
- Validation warnings/errors
- Preview of generated labels

**Actions:**
- "Download JSON" - exports complete VariantDefinition
- "Previous" / "Next" buttons for linear phase navigation

**Validation Checks:**
- All provinces have IDs and names
- All provinces have at least 1 adjacency
- Starting unit count matches for each nation
- SC count is reasonable for nation count
- No orphaned named coasts

---

## Key Algorithms

### SVG Parsing

```typescript
function parseSvg(svgString: string): ParsedSvg {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");

  // Get dimensions
  const svg = doc.querySelector("svg");
  const viewBox = svg?.getAttribute("viewBox")?.split(" ").map(Number);
  const dimensions = {
    width: viewBox?.[2] ?? parseFloat(svg?.getAttribute("width") ?? "1000"),
    height: viewBox?.[3] ?? parseFloat(svg?.getAttribute("height") ?? "1000"),
  };

  // Extract provinces layer
  const provincesLayer = findLayerByName(doc, "provinces");
  const provincePaths = Array.from(provincesLayer?.querySelectorAll("path") ?? [])
    .map(path => ({
      elementId: path.getAttribute("id"),
      d: path.getAttribute("d"),
      fill: path.getAttribute("fill"),
    }));

  // Extract named-coasts layer
  const coastsLayer = findLayerByName(doc, "named-coasts");
  const coastPaths = Array.from(coastsLayer?.querySelectorAll("path") ?? [])
    .map(path => ({
      elementId: path.getAttribute("id"),
      d: path.getAttribute("d"),
    }));

  // Extract text layer
  const textLayer = findLayerByName(doc, "text");
  const textElements = Array.from(textLayer?.querySelectorAll("text") ?? [])
    .map(text => ({
      content: text.textContent,
      x: parseFloat(text.getAttribute("x") ?? "0"),
      y: parseFloat(text.getAttribute("y") ?? "0"),
      styles: extractTextStyles(text),
    }));

  // Preserve other layers as decorative
  const decorativeElements = extractDecorativeLayers(doc, ["provinces", "named-coasts", "text"]);

  return { dimensions, provincePaths, coastPaths, textElements, decorativeElements };
}

function findLayerByName(doc: Document, name: string): Element | null {
  // Inkscape uses inkscape:label attribute for layer names
  return doc.querySelector(`g[inkscape\\:label="${name}"]`)
    ?? doc.querySelector(`g[id="${name}"]`);
}
```

### Adjacency Detection (Paper.js)

```typescript
import paper from "paper";

// Initialize Paper.js in headless mode (no canvas)
paper.setup(new paper.Size(1, 1));

function detectAdjacencies(provinces: { id: string; path: string }[]): Map<string, string[]> {
  const adjacencies = new Map<string, string[]>();

  // Create Paper.js paths for each province
  const paperPaths = provinces.map(p => ({
    id: p.id,
    path: new paper.Path(p.path),
  }));

  // Check each pair for intersection
  for (let i = 0; i < paperPaths.length; i++) {
    const adjacentIds: string[] = [];

    for (let j = 0; j < paperPaths.length; j++) {
      if (i === j) continue;

      const intersections = paperPaths[i].path.getIntersections(paperPaths[j].path);

      // If paths intersect at multiple points, they share a border
      if (intersections.length >= 2) {
        adjacentIds.push(paperPaths[j].id);
      }
    }

    adjacencies.set(paperPaths[i].id, adjacentIds);
  }

  return adjacencies;
}
```

### Centroid Calculation

```typescript
function calculateCentroid(pathD: string): { x: number; y: number } {
  const path = new paper.Path(pathD);

  // Use bounds center as a simple centroid
  // For complex shapes, could use area-weighted centroid
  const center = path.bounds.center;

  return { x: center.x, y: center.y };
}

function calculatePositions(centroid: { x: number; y: number }): {
  unitPosition: { x: number; y: number };
  dislodgedUnitPosition: { x: number; y: number };
  supplyCenterPosition: { x: number; y: number };
} {
  return {
    unitPosition: { x: centroid.x, y: centroid.y },
    dislodgedUnitPosition: { x: centroid.x + 15, y: centroid.y + 15 },
    supplyCenterPosition: { x: centroid.x - 12, y: centroid.y - 12 },
  };
}
```

### Text-Province Association

```typescript
function autoAssociateText(
  textElements: { content: string; x: number; y: number }[],
  provinces: { id: string; centroid: { x: number; y: number } }[]
): Map<number, string | null> {
  const associations = new Map<number, string | null>();
  const THRESHOLD = 100; // Max distance for auto-association

  textElements.forEach((text, index) => {
    let closestProvince: string | null = null;
    let closestDistance = Infinity;

    provinces.forEach(province => {
      const distance = Math.hypot(
        text.x - province.centroid.x,
        text.y - province.centroid.y
      );

      if (distance < closestDistance && distance < THRESHOLD) {
        closestDistance = distance;
        closestProvince = province.id;
      }
    });

    associations.set(index, closestProvince);
  });

  return associations;
}
```

### ID Suggestion from Name

```typescript
function suggestId(name: string): string {
  const words = name.trim().toLowerCase().split(/\s+/);

  if (words.length === 1) {
    // Single word: first 3 letters
    return words[0].slice(0, 3);
  } else {
    // Multiple words: first letter of each word
    return words.map(w => w[0]).join("").slice(0, 3);
  }
}

// Examples:
// "Berlin" → "ber"
// "North Sea" → "ns" (would need padding or different logic)
// "North Atlantic Ocean" → "nao"
// "St. Petersburg" → "sp" or "stp" (special case for abbreviations)
```

---

## File Structure

```
packages/variant-creator/
├── src/
│   ├── components/
│   │   ├── ui/                      # shadcn/ui components
│   │   ├── wizard/
│   │   │   ├── WizardLayout.tsx     # Phase navigation (prev/next)
│   │   │   ├── PhaseSetup.tsx       # Phase 0
│   │   │   ├── PhaseProvinces.tsx   # Phase 1 (table view + coast association)
│   │   │   ├── PhaseTextAssoc.tsx   # Phase 2
│   │   │   ├── PhaseAdjacencies.tsx # Phase 3
│   │   │   ├── PhaseVisualEditor.tsx# Phase 4
│   │   │   └── PhaseReview.tsx      # Phase 5
│   │   ├── map/
│   │   │   ├── MapCanvas.tsx        # SVG rendering
│   │   │   ├── ProvinceLayer.tsx    # Province paths with selection
│   │   │   ├── MarkerLayer.tsx      # Unit/SC/label markers
│   │   │   └── DraggableMarker.tsx  # Draggable position marker
│   │   └── common/
│   │       ├── ProvinceTable.tsx    # Spreadsheet component
│   │       ├── NationColorPicker.tsx
│   │       └── FileUpload.tsx
│   │
│   ├── hooks/
│   │   └── useVariant.ts            # Only stateful hook (state + localStorage)
│   │
│   ├── utils/
│   │   ├── svg.ts                   # SVG parsing (parseSvg, findLayerByName)
│   │   ├── geometry.ts              # Centroid, adjacency detection (Paper.js)
│   │   ├── textAssociation.ts       # Auto text-province linking
│   │   ├── idSuggestion.ts          # Name → ID conversion
│   │   ├── validation.ts            # Variant validation rules
│   │   └── export.ts                # JSON export
│   │
│   ├── types/
│   │   └── variant.ts               # TypeScript interfaces
│   │
│   ├── App.tsx                      # Main app with routing
│   ├── main.tsx                     # Entry point
│   └── index.css                    # Tailwind imports
│
├── public/
│   └── example-variant.svg          # Example SVG for testing
│
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── README.md
```

---

## State Management

### JSON as Source of Truth

```typescript
// hooks/useVariant.ts
import { useState, useEffect, useCallback } from "react";
import type { VariantDefinition } from "../types/variant";

const STORAGE_KEY = "variant-creator-draft";

export function useVariant() {
  const [variant, setVariant] = useState<VariantDefinition | null>(() => {
    // Load from localStorage on init
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  });

  // Auto-save to localStorage
  useEffect(() => {
    if (variant) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(variant));
    }
  }, [variant]);

  // Initialize from uploaded SVG
  const initFromSvg = useCallback((parsedSvg: ParsedSvg) => {
    setVariant(createInitialVariant(parsedSvg));
  }, []);

  // Initialize from uploaded JSON (resume editing)
  const initFromJson = useCallback((json: VariantDefinition) => {
    setVariant(json);
  }, []);

  // Update helpers
  const updateMetadata = useCallback((updates: Partial<VariantDefinition>) => {
    setVariant(prev => prev ? { ...prev, ...updates } : null);
  }, []);

  const updateProvince = useCallback((id: string, updates: Partial<Province>) => {
    setVariant(prev => {
      if (!prev) return null;
      return {
        ...prev,
        provinces: prev.provinces.map(p =>
          p.id === id ? { ...p, ...updates } : p
        ),
      };
    });
  }, []);

  const updateNation = useCallback((id: string, updates: Partial<Nation>) => {
    setVariant(prev => {
      if (!prev) return null;
      return {
        ...prev,
        nations: prev.nations.map(n =>
          n.id === id ? { ...n, ...updates } : n
        ),
      };
    });
  }, []);

  // Export
  const downloadJson = useCallback(() => {
    if (!variant) return;
    const blob = new Blob([JSON.stringify(variant, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${variant.name || "variant"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [variant]);

  // Clear draft
  const clearDraft = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setVariant(null);
  }, []);

  return {
    variant,
    initFromSvg,
    initFromJson,
    updateMetadata,
    updateProvince,
    updateNation,
    downloadJson,
    clearDraft,
  };
}
```

---

## SVG Re-Upload Workflow

When user modifies province paths in Inkscape and re-uploads:

1. Parse new SVG, extract province paths
2. Match new paths to existing provinces by element ID
3. Update path data in JSON, preserve all metadata
4. Show summary of changes

```typescript
function mergeUpdatedSvg(
  existingVariant: VariantDefinition,
  newSvg: ParsedSvg
): { variant: VariantDefinition; changes: ChangeReport } {
  const changes: ChangeReport = {
    updated: [],
    added: [],
    removed: [],
    unmatched: [],
  };

  const existingIds = new Set(existingVariant.provinces.map(p => p.id));
  const newPathsById = new Map(newSvg.provincePaths.map(p => [p.elementId, p]));

  // Update existing provinces with new paths
  const updatedProvinces = existingVariant.provinces.map(province => {
    const newPath = newPathsById.get(province.id);
    if (newPath) {
      changes.updated.push(province.id);
      return { ...province, path: newPath.d };
    }
    // Province exists in JSON but not in new SVG
    changes.removed.push(province.id);
    return province;
  });

  // Find new provinces (in SVG but not in JSON)
  newSvg.provincePaths.forEach(path => {
    if (path.elementId && !existingIds.has(path.elementId)) {
      changes.added.push(path.elementId);
    }
    if (!path.elementId || path.elementId.match(/^path\d+$/)) {
      changes.unmatched.push(path);
    }
  });

  return {
    variant: { ...existingVariant, provinces: updatedProvinces },
    changes,
  };
}
```

---

## Deployment

### Build

```bash
cd packages/variant-creator
npm run build
```

### Netlify Configuration

```toml
# netlify.toml
[build]
  base = "packages/variant-creator"
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Environment Variables

None required - app is fully client-side.

---

## Implementation Phases

Each phase is a complete, deployable increment. Phases must be completed sequentially, with manual testing in production before proceeding to the next phase.

### Implementation Phase 1: Walking Skeleton

**Goal:** Deployable "hello world" app with all infrastructure in place.

**Deliverables:**
- New `packages/variant-creator/` directory with Vite + React + TypeScript
- Tailwind CSS configured
- shadcn/ui initialized with Button component
- Landing page with "Variant Creator" heading and placeholder content
- Netlify deployment configured (auto-deploy on merge to main)
- Public URL accessible (e.g., `variant-creator.netlify.app`)

**Files to Create:**
- `packages/variant-creator/package.json`
- `packages/variant-creator/vite.config.ts`
- `packages/variant-creator/tsconfig.json`
- `packages/variant-creator/tailwind.config.js`
- `packages/variant-creator/index.html`
- `packages/variant-creator/src/main.tsx`
- `packages/variant-creator/src/App.tsx`
- `packages/variant-creator/src/index.css`
- `packages/variant-creator/netlify.toml`

**Testing:**
- Unit: None (no logic yet)
- Manual: Verify deployment succeeds and page loads at public URL

**Acceptance Criteria:**
- [ ] App builds without errors
- [ ] Netlify deployment succeeds on merge to main
- [ ] Public URL displays landing page

---

### Implementation Phase 2: SVG Upload & Validation

**Goal:** User can upload an SVG file and see validation feedback.

**Deliverables:**
- File upload component with drag-and-drop support
- SVG validation logic:
  - File is valid XML
  - Root element is `<svg>`
  - Contains `provinces` layer (required)
  - `provinces` layer contains at least one `<path>` element
- Error display for validation failures
- Success state showing "SVG valid" message

**Files to Create:**
- `packages/variant-creator/src/components/common/FileUpload.tsx`
- `packages/variant-creator/src/utils/svg.ts` (validation functions only)
- `packages/variant-creator/src/types/svg.ts`

**Testing:**
- Unit: `svg.ts` validation functions
  - Valid SVG with provinces layer passes
  - Missing provinces layer fails with specific error
  - Invalid XML fails
  - Non-SVG file fails
- RTL: FileUpload component renders, accepts files, shows errors

**Acceptance Criteria:**
- [ ] Can upload SVG via click or drag-and-drop
- [ ] Valid SVG shows success message
- [ ] Invalid SVG shows specific error message
- [ ] Non-SVG files are rejected

---

### Implementation Phase 3: SVG to Initial Variant State

**Goal:** Uploaded SVG is parsed into initial VariantDefinition state.

**Deliverables:**
- Complete SVG parsing implementation:
  - Extract dimensions from viewBox/width/height
  - Extract province paths from `provinces` layer
  - Extract coast paths from `named-coasts` layer (if present)
  - Extract text elements from `text` layer (if present)
  - Preserve other layers as decorative elements
- Initial VariantDefinition creation with defaults:
  - Empty metadata (name, description, author)
  - Empty nations array
  - Provinces with: temporary IDs, empty names, type "land", no adjacencies
  - Calculated positions (centroid-based)
- Display parsed province count and map preview

**Files to Create/Modify:**
- `packages/variant-creator/src/utils/svg.ts` (add parsing functions)
- `packages/variant-creator/src/utils/geometry.ts` (centroid calculation)
- `packages/variant-creator/src/types/variant.ts`
- `packages/variant-creator/src/components/map/MapCanvas.tsx` (basic SVG display)

**Dependencies:**
- Paper.js for geometry operations

**Testing:**
- Unit: `svg.ts` parsing functions
  - Extracts correct number of provinces
  - Handles missing optional layers
  - Extracts text with positions and styles
- Unit: `geometry.ts` centroid calculation
- RTL: After upload, shows province count and map preview

**Acceptance Criteria:**
- [ ] SVG upload creates VariantDefinition with correct province count
- [ ] Map preview displays all province paths
- [ ] Centroid positions are calculated for each province
- [ ] Text elements are extracted with position data

---

### Implementation Phase 4: Variant State Persistence

**Goal:** Variant state persists across page reloads.

**Deliverables:**
- `useVariant` hook with localStorage integration
- Auto-save on every state change
- Load existing draft on app initialization
- "Clear Draft" button to start fresh
- Visual indicator when draft exists

**Files to Create:**
- `packages/variant-creator/src/hooks/useVariant.ts`

**Testing:**
- Unit: useVariant hook
  - Saves to localStorage on state change
  - Loads from localStorage on init
  - clearDraft removes from localStorage
- RTL: Reload page, verify state persists

**Acceptance Criteria:**
- [ ] Upload SVG, refresh page → state is preserved
- [ ] Make edits, refresh page → edits are preserved
- [ ] Clear Draft button removes saved state
- [ ] Starting fresh shows no existing draft

---

### Implementation Phase 5: JSON Download

**Goal:** User can download current variant state as JSON file.

**Deliverables:**
- "Download JSON" button
- JSON export with pretty formatting
- Filename based on variant name (or "variant.json" if unnamed)

**Files to Create:**
- `packages/variant-creator/src/utils/export.ts`

**Testing:**
- Unit: export function produces valid JSON
- RTL: Click download button, verify blob creation

**Acceptance Criteria:**
- [ ] Download button creates JSON file
- [ ] JSON is valid and pretty-printed
- [ ] Filename reflects variant name

---

### Implementation Phase 6: JSON Upload

**Goal:** User can upload existing variant JSON to resume editing.

**Deliverables:**
- JSON upload option on landing page
- Zod schema validation for VariantDefinition
- Error display for invalid JSON
- Confirmation dialog if draft exists ("Replace current draft?")

**Files to Create:**
- `packages/variant-creator/src/utils/validation.ts` (Zod schemas)

**Testing:**
- Unit: Zod schema validates correct structure, rejects invalid
- RTL: Upload valid JSON, verify state loads
- RTL: Upload invalid JSON, verify error message

**Acceptance Criteria:**
- [ ] Can upload previously downloaded JSON
- [ ] Invalid JSON shows validation errors
- [ ] Existing draft prompts for confirmation before replacing

---

### Implementation Phase 7: Wizard Phase 0 - Variant Setup

**Goal:** User can define variant metadata and nations.

**Deliverables:**
- WizardLayout component with phase navigation
- URL-based routing (`/phase/0`, `/phase/1`, etc.)
- Phase 0 form:
  - Variant name, description, author inputs
  - Solo victory SC count input
  - Dynamic nation list with add/remove
  - Color picker for each nation
- Validation:
  - At least 2 nations
  - Unique nation names
  - Victory SC count > 0
- Next button (disabled until valid)

**Files to Create:**
- `packages/variant-creator/src/components/wizard/WizardLayout.tsx`
- `packages/variant-creator/src/components/wizard/PhaseSetup.tsx`
- `packages/variant-creator/src/components/common/NationColorPicker.tsx`

**Testing:**
- Unit: Validation logic for nations and metadata
- RTL: Form submission, validation errors, nation add/remove

**Acceptance Criteria:**
- [ ] Can enter variant metadata
- [ ] Can add/remove nations with colors
- [ ] Validation prevents proceeding with invalid data
- [ ] URL reflects current phase

---

### Implementation Phase 8: Wizard Phase 1 - Province Details

**Goal:** User can define metadata for each province.

**Deliverables:**
- Spreadsheet/table view of all provinces
- Per-province fields: ID, name, type, home nation, supply center, starting unit
- Map interaction:
  - Hover row → highlight province (temporary)
  - Click row → select province (persistent)
- Auto-suggestions:
  - ID from name (e.g., "Berlin" → "ber")
- Validation:
  - Unique 3-letter IDs
  - Fleet not on land-only, Army not on sea
  - Starting units only on home supply centers
- Coast association UI for "namedCoasts" type

**Files to Create:**
- `packages/variant-creator/src/components/wizard/PhaseProvinces.tsx`
- `packages/variant-creator/src/components/common/ProvinceTable.tsx`
- `packages/variant-creator/src/components/map/ProvinceLayer.tsx`
- `packages/variant-creator/src/utils/idSuggestion.ts`

**Testing:**
- Unit: ID suggestion algorithm
- Unit: Province validation rules
- RTL: Table editing, map highlighting, validation errors

**Acceptance Criteria:**
- [ ] All provinces displayed in table
- [ ] Can edit all province fields
- [ ] Map highlights on hover/select
- [ ] Validation prevents invalid configurations
- [ ] Named coasts can be associated with parent provinces

---

### Implementation Phase 9: Wizard Phase 2 - Text Association

**Goal:** User can link SVG text elements to provinces.

**Deliverables:**
- Table of text elements with province dropdown
- Map showing text elements (clickable)
- Auto-detection based on proximity to centroids
- Click text on map → select in table
- Click province on map → associate with selected text

**Files to Create:**
- `packages/variant-creator/src/components/wizard/PhaseTextAssoc.tsx`
- `packages/variant-creator/src/utils/textAssociation.ts`

**Testing:**
- Unit: Auto-association algorithm
- RTL: Text selection, province association, map interaction

**Acceptance Criteria:**
- [ ] All text elements listed
- [ ] Auto-detection pre-populates likely associations
- [ ] Can manually override associations
- [ ] Multiple texts can associate with same province

---

### Implementation Phase 10: Wizard Phase 3 - Adjacencies

**Goal:** User can define which provinces connect to each other.

**Deliverables:**
- Province-by-province adjacency editor
- Map with current province highlighted
- Click provinces to toggle adjacency
- Auto-detection using Paper.js path intersections
- Bidirectional enforcement (automatic)
- Progress indicator ("Province 34 of 81")
- Warning for isolated provinces

**Files to Create:**
- `packages/variant-creator/src/components/wizard/PhaseAdjacencies.tsx`
- `packages/variant-creator/src/utils/geometry.ts` (add adjacency detection)

**Testing:**
- Unit: Adjacency detection algorithm
- Unit: Bidirectional enforcement
- RTL: Province navigation, toggle adjacencies, warnings

**Acceptance Criteria:**
- [ ] Auto-detection identifies adjacent provinces
- [ ] Can manually add/remove adjacencies
- [ ] Adjacencies are always bidirectional
- [ ] Warning shown for provinces with no adjacencies

---

### Implementation Phase 11: Wizard Phase 4 - Visual Editor

**Goal:** User can adjust all positions and edit labels.

**Deliverables:**
- Map canvas with all markers visible:
  - Unit positions
  - Dislodged unit positions
  - Supply center positions
  - Labels (SVG + generated)
- Drag to reposition any element
- Double-click label to edit text
- Rotation handle/input for labels
- Visibility toggles by element type
- "Reset to Auto" per element
- "Accept All" to complete

**Files to Create:**
- `packages/variant-creator/src/components/wizard/PhaseVisualEditor.tsx`
- `packages/variant-creator/src/components/map/MarkerLayer.tsx`
- `packages/variant-creator/src/components/map/DraggableMarker.tsx`

**Dependencies:**
- @dnd-kit or pointer events for drag

**Testing:**
- RTL: Drag interactions, label editing, visibility toggles

**Acceptance Criteria:**
- [ ] All position markers visible on map
- [ ] Can drag any marker to new position
- [ ] Can edit label text and rotation
- [ ] Can toggle visibility by type
- [ ] Reset to Auto restores calculated position

---

### Implementation Phase 12: Wizard Phase 5 - Review & Export

**Goal:** User can review variant and download final JSON.

**Deliverables:**
- Summary statistics:
  - Province count, SC count
  - Nation breakdown (provinces, SCs, starting units per nation)
- Validation display:
  - Errors (blocking): missing IDs, orphaned coasts
  - Warnings (non-blocking): isolated provinces, unbalanced nations
- "Download JSON" button (same as Phase 5, but prominent)
- Navigation back to any previous phase

**Files to Create:**
- `packages/variant-creator/src/components/wizard/PhaseReview.tsx`
- `packages/variant-creator/src/utils/validation.ts` (add variant validation)

**Testing:**
- Unit: Validation rules (all checks from spec)
- RTL: Summary display, validation messages, download

**Acceptance Criteria:**
- [ ] Summary shows accurate statistics
- [ ] All validation errors/warnings displayed
- [ ] Can download final JSON
- [ ] Can navigate back to fix issues

---

### Phase Dependencies

```
Phase 1 (Walking Skeleton)
    ↓
Phase 2 (SVG Upload & Validation)
    ↓
Phase 3 (SVG to Variant State)
    ↓
Phase 4 (State Persistence)
    ↓
Phase 5 (JSON Download)
    ↓
Phase 6 (JSON Upload)
    ↓
Phase 7 (Wizard Phase 0: Setup)
    ↓
Phase 8 (Wizard Phase 1: Provinces)
    ↓
Phase 9 (Wizard Phase 2: Text)
    ↓
Phase 10 (Wizard Phase 3: Adjacencies)
    ↓
Phase 11 (Wizard Phase 4: Visual Editor)
    ↓
Phase 12 (Wizard Phase 5: Review)
```

### Testing Standards

**Every phase must include:**
1. **Unit tests** for utility functions and business logic
2. **RTL tests** for user interactions and component behavior
3. **Manual production testing** before proceeding to next phase

**Test file naming:**
- `src/utils/__tests__/svg.test.ts`
- `src/components/wizard/__tests__/PhaseSetup.test.tsx`

---

## Future Enhancements

### Sandbox Preview Integration

Add a "Preview in Sandbox" button that opens the main diplicity app with the variant loaded for playtesting:

```typescript
const previewInSandbox = () => {
  const encoded = btoa(JSON.stringify(variant));
  window.open(`https://diplicity.app/sandbox?variant=${encoded}`, "_blank");
};
```

The main app would detect the `variant` query param and load it client-side.

### Variant Submission

Add integration with GitHub to create a pull request or issue with the variant JSON attached.

### Collaborative Editing

Use a real-time collaboration library (e.g., Yjs) to enable multiple authors to work on a variant simultaneously.

---

## Open Questions

1. **Adjacency for named coasts:** Named coasts have different adjacencies than their parent. Should Phase 3 show these separately, or inline with the parent province?

2. **Variant versioning:** Should the JSON include a schema version for forward compatibility?
