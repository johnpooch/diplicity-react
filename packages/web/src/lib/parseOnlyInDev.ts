import { type ZodType } from "zod";

export function parseOnlyInDev<T>(schema: ZodType<T>, data: unknown): T {
  if (import.meta.env.DEV) {
    const result = schema.safeParse(data);
    if (!result.success) {
      console.error("Schema validation failed:", result.error);
    }
  }
  return data as T;
}
