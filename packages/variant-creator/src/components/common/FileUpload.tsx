import { useState, useRef } from "react";
import { Upload, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { validateSvg } from "@/utils/svg";
import type { SvgValidationResult } from "@/types/svg";

interface FileUploadProps {
  onFileValidated?: (result: SvgValidationResult, svgContent: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileValidated }) => {
  const [validationResult, setValidationResult] =
    useState<SvgValidationResult | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".svg")) {
      const result: SvgValidationResult = {
        valid: false,
        error: {
          code: "INVALID_XML",
          message: "Please upload an SVG file",
        },
      };
      setValidationResult(result);
      onFileValidated?.(result, "");
      return;
    }

    const content = await file.text();
    const result = validateSvg(content);
    setValidationResult(result);
    onFileValidated?.(result, content);
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
            <p className="text-green-600 font-medium">SVG valid!</p>
          </>
        ) : validationResult?.valid === false ? (
          <>
            <AlertCircle className="h-12 w-12 text-destructive" />
            <p className="text-destructive font-medium">
              {validationResult.error.message}
            </p>
          </>
        ) : (
          <>
            <Upload className="h-12 w-12 text-muted-foreground" />
            <p className="text-muted-foreground text-center">
              Drop SVG file here or click to upload
            </p>
          </>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".svg"
        onChange={handleFileSelect}
        className="hidden"
        aria-label="Upload SVG file"
      />
    </div>
  );
};
