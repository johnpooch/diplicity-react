import { FileUpload } from "@/components/common/FileUpload";
import { MapCanvas } from "@/components/map/MapCanvas";
import { Button } from "@/components/ui/button";
import { useVariant } from "@/hooks/useVariant";
import { downloadVariantJson } from "@/utils/export";
import { parseSvg } from "@/utils/svg";
import { createInitialVariant } from "@/utils/variantFactory";
import type { SvgValidationResult } from "@/types/svg";

function App() {
  const { variant, setVariant, clearDraft } = useVariant();

  const handleFileValidated = (
    result: SvgValidationResult,
    svgContent: string
  ) => {
    if (result.valid) {
      const parsed = parseSvg(svgContent);
      const initialVariant = createInitialVariant(parsed);
      setVariant(initialVariant);
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
            <div className="mb-4 flex items-center justify-between">
              <p className="text-lg font-medium">
                {variant.provinces.length} provinces detected
              </p>
              <div className="flex gap-2">
                <Button onClick={() => downloadVariantJson(variant)}>
                  Download JSON
                </Button>
                <Button variant="outline" onClick={clearDraft}>
                  Clear Draft
                </Button>
              </div>
            </div>
            <MapCanvas variant={variant} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
