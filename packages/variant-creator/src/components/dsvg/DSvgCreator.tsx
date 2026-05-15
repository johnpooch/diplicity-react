import { useState, useRef } from "react";
import { Upload, AlertCircle, X, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { LayerAssignment } from "@/components/dsvg/LayerAssignment";
import { LayerPreview } from "@/components/dsvg/LayerPreview";
import { NamedCoastEditor } from "@/components/dsvg/NamedCoastEditor";
import { DsvgExport } from "@/components/dsvg/DsvgExport";
import { parseSvgTree, validateAnySvg } from "@/utils/svgTree";
import type { SvgTreeNode } from "@/utils/svgTree";
import type { LayerAssignments } from "@/components/dsvg/LayerAssignment";
import type { LayerPreviewHandle } from "@/components/dsvg/LayerPreview";
import type { NamedCoastEditorHandle } from "@/components/dsvg/NamedCoastEditor";

type Step = "upload" | "assign" | "preview" | "named-coasts" | "done";

const DEFAULT_ASSIGNMENTS: LayerAssignments = {
  provinces: null,
  namedCoasts: null,
  provinceNames: null,
  borders: null,
};

const STEP_TITLES: Record<Exclude<Step, "upload">, string> = {
  assign: "Assign layers",
  preview: "Province abbreviations",
  "named-coasts": "Named coasts",
  done: "Review & export",
};

const STEP_SUBTITLES: Record<Exclude<Step, "upload">, string> = {
  assign: "Map your SVG layers to the four named layers.",
  preview: "Review layers and set province abbreviations.",
  "named-coasts": "Assign parent provinces and abbreviations to each named coast.",
  done: "Toggle layer visibility and download your dSVG file.",
};

const PREV_STEP: Record<Exclude<Step, "upload">, Step> = {
  assign: "upload",
  preview: "assign",
  "named-coasts": "preview",
  done: "named-coasts",
};

export function DSvgCreator() {
  const [step, setStep] = useState<Step>("upload");
  const [svgContent, setSvgContent] = useState<string | null>(null);
  const [tree, setTree] = useState<SvgTreeNode[] | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [assignments, setAssignments] =
    useState<LayerAssignments>(DEFAULT_ASSIGNMENTS);
  const [provinceAbbrs, setProvinceAbbrs] = useState<Record<string, string>>(
    {}
  );

  const fileInputRef = useRef<HTMLInputElement>(null);
  const layerPreviewRef = useRef<LayerPreviewHandle>(null);
  const namedCoastEditorRef = useRef<NamedCoastEditorHandle>(null);

  const processFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".svg")) {
      setError("Please upload an SVG file.");
      return;
    }

    const content = await file.text();
    const validationError = validateAnySvg(content);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setFileName(file.name);
    setSvgContent(content);
    setTree(parseSvgTree(content));
    setAssignments(DEFAULT_ASSIGNMENTS);
    setProvinceAbbrs({});
    setStep("assign");
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const handleClear = () => {
    setStep("upload");
    setSvgContent(null);
    setTree(null);
    setFileName(null);
    setError(null);
    setAssignments(DEFAULT_ASSIGNMENTS);
    setProvinceAbbrs({});
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleNext = () => {
    if (step === "assign") {
      setStep("preview");
      return;
    }
    if (step === "preview") {
      const abbrs = layerPreviewRef.current?.validate();
      if (abbrs) {
        setProvinceAbbrs(abbrs);
        setStep("named-coasts");
      }
      return;
    }
    if (step === "named-coasts") {
      setStep("done");
      return;
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center p-8">
      <div className="flex w-full max-w-5xl flex-col gap-6">
        {step === "upload" ? (
          <>
            <div>
              <h1 className="text-3xl font-bold">dSVG Creator</h1>
              <p className="mt-1 text-muted-foreground">Upload an SVG to begin.</p>
            </div>

            <div
              role="button"
              tabIndex={0}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={e => {
                if (e.key === "Enter" || e.key === " ")
                  fileInputRef.current?.click();
              }}
              onDrop={handleDrop}
              onDragOver={e => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={e => {
                e.preventDefault();
                setIsDragging(false);
              }}
              className={cn(
                "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-12 transition-colors",
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-muted-foreground/25 hover:border-muted-foreground/50"
              )}
            >
              <Upload className="h-10 w-10 text-muted-foreground" />
              <p className="text-center text-muted-foreground">
                Drop any SVG here or click to upload
              </p>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}
          </>
        ) : (
          <>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold">
                  {STEP_TITLES[step as Exclude<Step, "upload">]}
                </h1>
                <p className="mt-1 text-muted-foreground">
                  {STEP_SUBTITLES[step as Exclude<Step, "upload">]}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3 pt-1">
                <span className="text-sm text-muted-foreground">{fileName}</span>
                <Button variant="ghost" size="sm" onClick={handleClear}>
                  <X className="h-4 w-4" />
                  Clear
                </Button>
              </div>
            </div>

            {step === "assign" && tree && (
              <LayerAssignment
                tree={tree}
                assignments={assignments}
                onChange={setAssignments}
              />
            )}

            {step === "preview" && svgContent && (
              <LayerPreview
                ref={layerPreviewRef}
                svgContent={svgContent}
                assignments={assignments}
              />
            )}

            {step === "named-coasts" && svgContent && (
              <NamedCoastEditor
                ref={namedCoastEditorRef}
                svgContent={svgContent}
                assignments={assignments}
                provinceAbbrs={provinceAbbrs}
              />
            )}

            {step === "done" && svgContent && tree && (
              <DsvgExport
                svgContent={svgContent}
                assignments={assignments}
                tree={tree}
                fileName={fileName ?? "map.svg"}
              />
            )}

            <div className="flex justify-between pt-2">
              <Button
                variant="outline"
                onClick={() =>
                  setStep(PREV_STEP[step as Exclude<Step, "upload">])
                }
              >
                <ChevronLeft className="h-4 w-4" />
                Back
              </Button>

              {step !== "done" && (
                <Button onClick={handleNext}>
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              )}
            </div>
          </>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".svg"
          onChange={handleFileSelect}
          className="hidden"
          aria-label="Upload SVG file"
        />
      </div>
    </div>
  );
}
