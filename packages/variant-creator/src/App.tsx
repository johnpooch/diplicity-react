import { useState } from "react";
import { FileUpload } from "@/components/common/FileUpload";
import { MapCanvas } from "@/components/map/MapCanvas";
import { parseSvg } from "@/utils/svg";
import { createInitialVariant } from "@/utils/variantFactory";
import type { SvgValidationResult } from "@/types/svg";
import type { VariantDefinition } from "@/types/variant";

function App() {
  const [variant, setVariant] = useState<VariantDefinition | null>(null);

  const handleFileValidated = (
    result: SvgValidationResult,
    svgContent: string
  ) => {
    if (result.valid) {
      const parsed = parseSvg(svgContent);
      const initialVariant = createInitialVariant(parsed);
      setVariant(initialVariant);
    } else {
      setVariant(null);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center p-8">
      <div className="flex w-full max-w-4xl flex-col items-center text-center">
        <h1 className="mb-4 text-4xl font-bold">Diplicity Variant Creator</h1>
        <p className="mb-8 text-lg text-muted-foreground">
          Create custom Diplomacy variants using Inkscape SVG files. Upload your
          map, define provinces and nations, and export a complete variant
          definition.
        </p>
        <FileUpload onFileValidated={handleFileValidated} />

        {variant && (
          <div className="mt-8 w-full">
            <p className="mb-4 text-lg font-medium">
              {variant.provinces.length} provinces detected
            </p>
            <MapCanvas variant={variant} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
