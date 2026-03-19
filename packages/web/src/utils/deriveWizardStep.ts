import type { FieldValue, FlatOrderOption } from "../api/generated/endpoints";

export type { FieldValue };
export type OrderOption = FlatOrderOption;

export type FieldName =
  | "source"
  | "orderType"
  | "target"
  | "aux"
  | "unitType"
  | "namedCoast";

export interface WizardStep {
  nextField: FieldName | null;
  choices: FieldValue[];
  isComplete: boolean;
  selectedArray: string[];
  resolvedSelections: Record<string, string>;
}

const UNIVERSAL_PREFIX: FieldName[] = ["source", "orderType"];

function filterOrders(
  orders: OrderOption[],
  selections: Record<string, string>
): OrderOption[] {
  return orders.filter((order) =>
    Object.entries(selections).every(
      ([field, id]) => order[field as FieldName]?.id === id
    )
  );
}

function distinctByIdFirstOccurrence(values: FieldValue[]): FieldValue[] {
  const seen = new Set<string>();
  const result: FieldValue[] = [];
  for (const v of values) {
    if (!seen.has(v.id)) {
      seen.add(v.id);
      result.push(v);
    }
  }
  return result;
}

export function deriveWizardStep(
  orders: OrderOption[],
  fieldOrder: Record<string, FieldName[]>,
  selections: Record<string, string>
): WizardStep {
  const resolvedSelections: Record<string, string> = { ...selections };

  // Handle empty orders early
  if (orders.length === 0) {
    return {
      nextField: null,
      choices: [],
      isComplete: false,
      selectedArray: [],
      resolvedSelections,
    };
  }

  let filtered = filterOrders(orders, resolvedSelections);

  // Walk until we find a nextField or complete
  // We may loop multiple times as auto-advances update resolvedSelections and re-filter
  let iterations = 0;
  while (iterations < 20 && filtered.length > 0) {
    iterations++;

    const orderTypeId = resolvedSelections["orderType"];
    const sequence: FieldName[] = orderTypeId
      ? (fieldOrder[orderTypeId] ?? UNIVERSAL_PREFIX)
      : UNIVERSAL_PREFIX;

    let foundNextField = false;

    for (const field of sequence) {
      if (resolvedSelections[field] !== undefined) {
        continue;
      }

      const allNull = filtered.every((o) => o[field] === null);
      if (allNull) {
        continue;
      }

      const nonNullValues = filtered
        .map((o) => o[field])
        .filter((v): v is FieldValue => v !== null);
      const distinct = distinctByIdFirstOccurrence(nonNullValues);

      if (distinct.length === 0) {
        // Shouldn't happen with valid data — treat as complete
        break;
      }

      if (distinct.length === 1) {
        // Auto-advance: record and re-filter
        resolvedSelections[field] = distinct[0].id;
        filtered = filterOrders(orders, resolvedSelections);
        foundNextField = false;
        // Restart the sequence walk (break inner loop, re-run outer while)
        break;
      }

      // Multiple choices — this is the next field
      return {
        nextField: field,
        choices: distinct,
        isComplete: false,
        selectedArray: buildSelectedArray(fieldOrder, resolvedSelections),
        resolvedSelections,
      };
    }

    if (foundNextField) {
      break;
    }

    // Check if we completed the sequence (no new auto-advances happened this iteration)
    const orderTypeIdNow = resolvedSelections["orderType"];
    const sequenceNow: FieldName[] = orderTypeIdNow
      ? (fieldOrder[orderTypeIdNow] ?? UNIVERSAL_PREFIX)
      : UNIVERSAL_PREFIX;

    const allResolved = sequenceNow.every(
      (field) =>
        resolvedSelections[field] !== undefined ||
        filtered.every((o) => o[field] === null)
    );

    if (allResolved) {
      return {
        nextField: null,
        choices: [],
        isComplete: true,
        selectedArray: buildSelectedArray(fieldOrder, resolvedSelections),
        resolvedSelections,
      };
    }

    // If we got here without finding a nextField and without completing,
    // we must have auto-advanced at least one field — loop again
  }

  // Fallback (shouldn't normally reach here)
  return {
    nextField: null,
    choices: [],
    isComplete: false,
    selectedArray: buildSelectedArray(fieldOrder, resolvedSelections),
    resolvedSelections,
  };
}

function buildSelectedArray(
  fieldOrder: Record<string, FieldName[]>,
  resolvedSelections: Record<string, string>
): string[] {
  const orderTypeId = resolvedSelections["orderType"];
  if (!orderTypeId) {
    return [];
  }
  const sequence = fieldOrder[orderTypeId];
  if (!sequence) {
    return [];
  }
  return sequence
    .map((field) => resolvedSelections[field])
    .filter((v): v is string => v !== undefined);
}
