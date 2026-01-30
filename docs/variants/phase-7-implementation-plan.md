# Implementation Phase 7: Wizard Phase 0 - Variant Setup

## Overview

**Goal:** User can define variant metadata and nations through a wizard interface with URL-based routing.

**Current State:** Phase 6 is complete. The app has:
- SVG and JSON upload capabilities
- State persistence via `useVariant` hook with localStorage
- Map preview rendering
- JSON download functionality
- Basic UI components (Button, AlertDialog)

**What Phase 7 Adds:**
- React Router for URL-based wizard navigation
- WizardLayout component with phase progress indicator
- Phase 0 form for variant metadata and nation definitions
- Form validation with Zod
- Color picker for nations

---

## Implementation Tasks

### Task 1: Install Dependencies

Add React Router and additional shadcn/ui components needed for forms.

**Dependencies to add:**
- `react-router-dom` - URL-based routing
- shadcn/ui components: `input`, `label`, `card`, `form` (react-hook-form integration)
- `react-hook-form` - Form handling
- `@hookform/resolvers` - Zod resolver for react-hook-form

**Files to modify:**
- `packages/variant-creator/package.json`

---

### Task 2: Add shadcn/ui Form Components

Generate the required UI components for forms.

**Components to add:**
- `src/components/ui/input.tsx` - Text input field
- `src/components/ui/label.tsx` - Form labels
- `src/components/ui/card.tsx` - Card container for form sections
- `src/components/ui/form.tsx` - Form integration with react-hook-form

---

### Task 3: Set Up React Router

Configure routing for the wizard phases.

**Route Structure:**
```
/                    → Landing page (upload SVG/JSON or continue draft)
/phase/0             → Variant Setup (metadata + nations)
/phase/1             → Province Details
/phase/2             → Text Association
/phase/3             → Adjacencies
/phase/4             → Visual Editor
/phase/5             → Review & Export
```

**Files to create:**
- `src/Router.tsx` - Route definitions

**Files to modify:**
- `src/main.tsx` - Wrap App with BrowserRouter
- `src/App.tsx` - Refactor to use routing, move landing page content

---

### Task 4: Create WizardLayout Component

Layout wrapper for all wizard phases with navigation.

**Features:**
- Phase indicator showing current position (e.g., "Phase 1 of 6")
- Previous/Next navigation buttons
- Phase titles displayed
- Consistent layout container

**Props:**
```typescript
interface WizardLayoutProps {
  children: React.ReactNode;
  currentPhase: number;
  totalPhases: number;
  phaseTitle: string;
  canProceed: boolean;
  onNext: () => void;
  onPrevious: () => void;
  showPrevious?: boolean;
}
```

**Files to create:**
- `src/components/wizard/WizardLayout.tsx`

---

### Task 5: Enhance useVariant Hook

Add specific update methods for metadata and nations.

**Methods to add:**
```typescript
updateMetadata(updates: Partial<Pick<VariantDefinition, 'name' | 'description' | 'author' | 'soloVictorySCCount'>>): void
addNation(nation: Nation): void
updateNation(id: string, updates: Partial<Nation>): void
removeNation(id: string): void
```

**Files to modify:**
- `src/hooks/useVariant.ts`

---

### Task 6: Create NationColorPicker Component

Reusable component for selecting nation colors.

**Features:**
- Preset color palette (common Diplomacy nation colors)
- Custom color input (hex)
- Color preview swatch
- Accessible color contrast

**Props:**
```typescript
interface NationColorPickerProps {
  value: string;
  onChange: (color: string) => void;
  disabled?: boolean;
}
```

**Preset Colors:**
- England Blue: #2196F3
- France Cyan: #00BCD4
- Germany Gray: #607D8B
- Austria Red: #F44336
- Italy Green: #4CAF50
- Russia Purple: #9C27B0
- Turkey Yellow: #FFC107
- Additional neutrals

**Files to create:**
- `src/components/common/NationColorPicker.tsx`

---

### Task 7: Create PhaseSetup Component (Phase 0)

The main form for variant metadata and nation definitions.

**Sections:**

1. **Variant Metadata**
   - Name (text input, required)
   - Description (text area)
   - Author (text input)
   - Solo Victory SC Count (number input, min 1)

2. **Nations**
   - Dynamic list of nations
   - Each nation: name input + color picker + remove button
   - "Add Nation" button
   - Validation: at least 2 nations, unique names

**Form Validation Schema (Zod):**
```typescript
const phaseSetupSchema = z.object({
  name: z.string().min(1, "Variant name is required"),
  description: z.string().default(""),
  author: z.string().default(""),
  soloVictorySCCount: z.number().min(1, "Must be at least 1"),
  nations: z.array(z.object({
    id: z.string(),
    name: z.string().min(1, "Nation name is required"),
    color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, "Invalid color format"),
  })).min(2, "At least 2 nations required")
    .refine(
      nations => new Set(nations.map(n => n.name.toLowerCase())).size === nations.length,
      "Nation names must be unique"
    ),
});
```

**Files to create:**
- `src/components/wizard/PhaseSetup.tsx`
- `src/components/wizard/__tests__/PhaseSetup.test.tsx`

---

### Task 8: Create Landing Page Component

Extract landing page from App.tsx into its own component.

**Features:**
- "Start New Variant" section with SVG upload
- "Resume Editing" section with JSON upload
- "Continue Draft" button if draft exists in localStorage
- Clear draft option

**Files to create:**
- `src/components/LandingPage.tsx`

**Files to modify:**
- `src/App.tsx` - Import and use LandingPage

---

### Task 9: Update App.tsx for Routing

Integrate router and manage navigation between landing and wizard.

**Flow:**
1. Landing page: Upload SVG → redirect to `/phase/0`
2. Landing page: Upload JSON → redirect to `/phase/0`
3. Landing page: Continue Draft → redirect to `/phase/0`
4. Wizard phases: Next/Previous navigate between `/phase/N`

**Files to modify:**
- `src/App.tsx`

---

### Task 10: Write Tests

**Unit Tests:**
- Phase setup validation logic (Zod schema)
- Nation add/remove/update logic in useVariant
- ID generation for new nations

**RTL Tests:**
- PhaseSetup form rendering
- Adding and removing nations
- Validation error display
- Navigation disabled when invalid
- Form submission and state update

**Files to create:**
- `src/components/wizard/__tests__/PhaseSetup.test.tsx`
- `src/components/wizard/__tests__/WizardLayout.test.tsx`
- `src/components/common/__tests__/NationColorPicker.test.tsx`
- `src/hooks/__tests__/useVariant.test.ts` (update existing)

---

## Acceptance Criteria

- [ ] Can enter variant name, description, author
- [ ] Can set solo victory SC count (validates > 0)
- [ ] Can add nations with name and color
- [ ] Can remove nations (minimum 2 enforced)
- [ ] Nation names must be unique (case-insensitive)
- [ ] Next button disabled until form is valid
- [ ] URL shows `/phase/0` when on setup phase
- [ ] Previous button returns to landing page
- [ ] State persists to localStorage on changes
- [ ] All tests pass

---

## File Summary

### New Files
```
src/
├── Router.tsx
├── components/
│   ├── LandingPage.tsx
│   ├── common/
│   │   ├── NationColorPicker.tsx
│   │   └── __tests__/
│   │       └── NationColorPicker.test.tsx
│   ├── wizard/
│   │   ├── WizardLayout.tsx
│   │   ├── PhaseSetup.tsx
│   │   └── __tests__/
│   │       ├── WizardLayout.test.tsx
│   │       └── PhaseSetup.test.tsx
│   └── ui/
│       ├── input.tsx
│       ├── label.tsx
│       ├── card.tsx
│       └── form.tsx
```

### Modified Files
```
src/
├── main.tsx          # Add BrowserRouter
├── App.tsx           # Routing integration
└── hooks/
    └── useVariant.ts # Add update methods
```

---

## Implementation Order

1. **Task 1**: Install dependencies
2. **Task 2**: Add shadcn/ui form components
3. **Task 3**: Set up React Router (basic structure)
4. **Task 5**: Enhance useVariant hook
5. **Task 4**: Create WizardLayout component
6. **Task 6**: Create NationColorPicker component
7. **Task 8**: Create LandingPage component
8. **Task 7**: Create PhaseSetup component
9. **Task 9**: Integrate routing in App.tsx
10. **Task 10**: Write tests

This order ensures dependencies are in place before components that use them.
