import { z } from "zod";
import type { VariantDefinition } from "@/types/variant";

const PositionSchema = z.object({
  x: z.number(),
  y: z.number(),
});

const LabelStylesSchema = z.object({
  fontSize: z.string().optional(),
  fontFamily: z.string().optional(),
  fontWeight: z.string().optional(),
  fill: z.string().optional(),
});

const LabelSchema = z.object({
  text: z.string(),
  position: PositionSchema,
  rotation: z.number().optional(),
  source: z.enum(["svg", "generated"]),
  styles: LabelStylesSchema.optional(),
});

const StartingUnitSchema = z.object({
  type: z.enum(["Army", "Fleet"]),
});

const ProvinceSchema = z.object({
  id: z.string(),
  elementId: z.string(),
  name: z.string(),
  type: z.enum(["land", "sea", "coastal", "namedCoasts"]),
  path: z.string(),
  homeNation: z.string().nullable(),
  supplyCenter: z.boolean(),
  startingUnit: StartingUnitSchema.nullable(),
  adjacencies: z.array(z.string()),
  labels: z.array(LabelSchema),
  unitPosition: PositionSchema,
  dislodgedUnitPosition: PositionSchema,
  supplyCenterPosition: PositionSchema.optional(),
});

const NamedCoastSchema = z.object({
  id: z.string(),
  name: z.string(),
  parentId: z.string(),
  path: z.string(),
  adjacencies: z.array(z.string()),
  unitPosition: PositionSchema,
  dislodgedUnitPosition: PositionSchema,
});

const NationSchema = z.object({
  id: z.string(),
  name: z.string(),
  color: z.string(),
});

const DecorativeElementSchema = z.object({
  id: z.string(),
  type: z.enum(["path", "text", "group"]),
  content: z.string(),
  styles: z.record(z.string(), z.string()).optional(),
});

const DimensionsSchema = z.object({
  width: z.number().positive(),
  height: z.number().positive(),
});

export const VariantDefinitionSchema = z.object({
  name: z.string(),
  description: z.string(),
  author: z.string(),
  version: z.string(),
  soloVictorySCCount: z.number().nonnegative(),
  nations: z.array(NationSchema),
  provinces: z.array(ProvinceSchema),
  namedCoasts: z.array(NamedCoastSchema),
  decorativeElements: z.array(DecorativeElementSchema),
  dimensions: DimensionsSchema,
});

export type JsonValidationErrorCode =
  | "INVALID_JSON"
  | "INVALID_SCHEMA"
  | "EMPTY_PROVINCES";

export interface JsonValidationError {
  code: JsonValidationErrorCode;
  message: string;
  details?: string;
}

export type JsonValidationResult =
  | { valid: true; variant: VariantDefinition }
  | { valid: false; error: JsonValidationError };

export function validateVariantJson(jsonString: string): JsonValidationResult {
  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonString);
  } catch {
    return {
      valid: false,
      error: {
        code: "INVALID_JSON",
        message: "Invalid JSON format",
      },
    };
  }

  const result = VariantDefinitionSchema.safeParse(parsed);
  if (!result.success) {
    const firstIssue = result.error.issues[0];
    const path = firstIssue.path.join(".");
    return {
      valid: false,
      error: {
        code: "INVALID_SCHEMA",
        message: "Invalid variant structure",
        details: path ? `Error at "${path}": ${firstIssue.message}` : firstIssue.message,
      },
    };
  }

  if (result.data.provinces.length === 0) {
    return {
      valid: false,
      error: {
        code: "EMPTY_PROVINCES",
        message: "Variant must contain at least one province",
      },
    };
  }

  return {
    valid: true,
    variant: result.data as VariantDefinition,
  };
}
