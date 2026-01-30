import { useState, useRef } from "react";
import { FileJson, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { validateVariantJson, type JsonValidationResult } from "@/utils/validation";
import type { VariantDefinition } from "@/types/variant";

interface JsonUploadProps {
  onFileValidated?: (result: JsonValidationResult, variant: VariantDefinition | null) => void;
}

export const JsonUpload: React.FC<JsonUploadProps> = ({ onFileValidated }) => {
  const [validationResult, setValidationResult] =
    useState<JsonValidationResult | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".json")) {
      const result: JsonValidationResult = {
        valid: false,
        error: {
          code: "INVALID_JSON",
          message: "Please upload a JSON file",
        },
      };
      setValidationResult(result);
      onFileValidated?.(result, null);
      return;
    }

    const content = await file.text();
    const result = validateVariantJson(content);
    setValidationResult(result);
    onFileValidated?.(result, result.valid ? result.variant : null);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  return (
    <div className="w-full max-w-md">
      <div
        role="button"
        tabIndex={0}
        onClick={handleClick}
        onKeyDown={e => {
          if (e.key === "Enter" || e.key === " ") {
            handleClick();
          }
        }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          "flex flex-col items-center justify-center gap-4 p-8 border-2 border-dashed rounded-lg cursor-pointer transition-colors",
          isDragging && "border-primary bg-primary/5",
          validationResult?.valid === true &&
            "border-green-500 bg-green-500/5",
          validationResult?.valid === false && "border-destructive bg-destructive/5",
          !validationResult && !isDragging && "border-muted-foreground/25 hover:border-muted-foreground/50"
        )}
      >
        {validationResult?.valid === true ? (
          <>
            <CheckCircle className="h-12 w-12 text-green-500" />
            <p className="text-green-600 font-medium">JSON valid!</p>
          </>
        ) : validationResult?.valid === false ? (
          <>
            <AlertCircle className="h-12 w-12 text-destructive" />
            <div className="text-center">
              <p className="text-destructive font-medium">
                {validationResult.error.message}
              </p>
              {validationResult.error.details && (
                <p className="text-destructive/80 text-sm mt-1">
                  {validationResult.error.details}
                </p>
              )}
            </div>
          </>
        ) : (
          <>
            <FileJson className="h-12 w-12 text-muted-foreground" />
            <p className="text-muted-foreground text-center">
              Drop JSON file here or click to upload
            </p>
          </>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileSelect}
        className="hidden"
        aria-label="Upload JSON file"
      />
    </div>
  );
};
