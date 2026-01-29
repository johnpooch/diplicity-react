export type SvgValidationErrorCode =
  | "INVALID_XML"
  | "NOT_SVG"
  | "MISSING_PROVINCES_LAYER"
  | "EMPTY_PROVINCES_LAYER";

export interface SvgValidationError {
  code: SvgValidationErrorCode;
  message: string;
}

export interface SvgValidationSuccess {
  valid: true;
}

export interface SvgValidationFailure {
  valid: false;
  error: SvgValidationError;
}

export type SvgValidationResult = SvgValidationSuccess | SvgValidationFailure;
