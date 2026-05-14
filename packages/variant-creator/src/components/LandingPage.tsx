import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileUpload } from "@/components/common/FileUpload";
import { JsonUpload } from "@/components/common/JsonUpload";
import { MapCanvas } from "@/components/map/MapCanvas";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useVariant } from "@/hooks/useVariant";
import { downloadVariantJson } from "@/utils/export";
import { parseSvg, extractLayerTree, flattenLayerTree } from "@/utils/svg";
import { createInitialVariant } from "@/utils/variantFactory";
import { LayerMappingDialog } from "@/components/common/LayerMappingDialog";
import type { SvgValidationResult } from "@/types/svg";
import type { JsonValidationResult } from "@/utils/validation";
import type { VariantDefinition } from "@/types/variant";
import type { LayerNameMapping, SvgLayer } from "@/utils/svg";

export function LandingPage() {
  const navigate = useNavigate();
  const { variant, setVariant, clearDraft, setRawSvg } = useVariant();
  const [pendingVariant, setPendingVariant] =
    useState<VariantDefinition | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingSvgContent, setPendingSvgContent] = useState<string | null>(null);
  const [pendingLayerNames, setPendingLayerNames] = useState<SvgLayer[]>([]);
  const [showLayerMappingDialog, setShowLayerMappingDialog] = useState(false);

  const applyVariant = (newVariant: VariantDefinition) => {
    if (variant) {
      setPendingVariant(newVariant);
      setShowConfirmDialog(true);
    } else {
      setVariant(newVariant);
      navigate("/phase/0");
    }
  };

  const parseSvgAndApply = (svgContent: string, mapping?: LayerNameMapping) => {
    const parsed = parseSvg(svgContent, mapping);
    const initialVariant = createInitialVariant(parsed);
    setRawSvg(svgContent);
    applyVariant(initialVariant);
  };

  const handleSvgFileValidated = (
    result: SvgValidationResult,
    svgContent: string
  ) => {
    if (!result.valid) return;

    const layerTree = extractLayerTree(svgContent);
    const flatLayers = flattenLayerTree(layerTree);
    const hasProvinces = flatLayers.some((l) => l.name === "provinces");
    const hasText = flatLayers.some((l) => l.name === "text");

    if (hasProvinces && hasText) {
      parseSvgAndApply(svgContent);
    } else {
      setPendingSvgContent(svgContent);
      setPendingLayerNames(layerTree);
      setShowLayerMappingDialog(true);
    }
  };

  const handleLayerMappingConfirm = (mapping: LayerNameMapping) => {
    setShowLayerMappingDialog(false);
    if (pendingSvgContent) {
      parseSvgAndApply(pendingSvgContent, mapping);
      setPendingSvgContent(null);
    }
  };

  const handleLayerMappingCancel = () => {
    setShowLayerMappingDialog(false);
    setPendingSvgContent(null);
  };

  const handleJsonFileValidated = (
    result: JsonValidationResult,
    uploadedVariant: VariantDefinition | null
  ) => {
    if (result.valid && uploadedVariant) {
      applyVariant(uploadedVariant);
    }
  };

  const handleConfirmReplace = () => {
    if (pendingVariant) {
      setVariant(pendingVariant);
      setPendingVariant(null);
      navigate("/phase/0");
    }
    setShowConfirmDialog(false);
  };

  const handleCancelReplace = () => {
    setPendingVariant(null);
    setShowConfirmDialog(false);
  };

  const handleContinueDraft = () => {
    navigate("/phase/0");
  };

  return (
    <div className="flex min-h-screen flex-col items-center p-8">
      <div className="flex w-full max-w-4xl flex-col items-center text-center">
        <h1 className="mb-4 text-4xl font-bold">Diplicity Variant Creator</h1>
        <p className="mb-8 text-lg text-muted-foreground">
          Create custom Diplomacy variants using SVG files. Upload your
          map, define provinces and nations, and export a complete variant
          definition.
        </p>

        <div className="flex w-full flex-col items-center gap-6 sm:flex-row sm:justify-center">
          <div className="flex flex-col items-center gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">
              Start from SVG
            </h2>
            <FileUpload onFileValidated={handleSvgFileValidated} />
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="h-px w-8 bg-border sm:h-8 sm:w-px" />
            <span className="text-sm">or</span>
            <div className="h-px w-8 bg-border sm:h-8 sm:w-px" />
          </div>
          <div className="flex flex-col items-center gap-2">
            <h2 className="text-sm font-medium text-muted-foreground">
              Resume from JSON
            </h2>
            <JsonUpload onFileValidated={handleJsonFileValidated} />
          </div>
        </div>

        {variant && (
          <div className="mt-8 w-full">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-lg font-medium">
                {variant.provinces.length} provinces detected
              </p>
              <div className="flex gap-2">
                <Button onClick={handleContinueDraft}>Continue Editing</Button>
                <Button
                  variant="outline"
                  onClick={() => downloadVariantJson(variant)}
                >
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

      {showLayerMappingDialog && (
        <LayerMappingDialog
          open={showLayerMappingDialog}
          layers={pendingLayerNames}
          onConfirm={handleLayerMappingConfirm}
          onCancel={handleLayerMappingCancel}
        />
      )}

      <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Replace current draft?</AlertDialogTitle>
            <AlertDialogDescription>
              You have an existing draft with {variant?.provinces.length}{" "}
              provinces. This will replace it with the new upload. This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelReplace}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmReplace}>
              Replace
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
