import React, { Suspense } from "react";
import { Link, useNavigate } from "react-router";
import { Download, FilePlus, Pencil, Play, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { ScreenContainer } from "@/components/ui/screen-container";
import { ScreenHeader } from "@/components/ui/screen-header";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Notice } from "@/components/Notice";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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

import {
  useVariantsListSuspense,
  useVariantsDestroy,
  useSandboxGameCreate,
  getVariantsListQueryKey,
  Variant,
} from "@/api/generated/endpoints";
import { MapPreview } from "@/components/MapPreview";
import axiosInstance from "@/api/axiosInstance";
import { useQueryClient } from "@tanstack/react-query";

const statusLabel: Record<string, string> = {
  draft: "Draft",
  published: "Published",
  archived: "Archived",
};

const statusVariant: Record<string, "default" | "secondary" | "outline"> = {
  draft: "outline",
  published: "default",
  archived: "secondary",
};

const downloadFile = (data: BlobPart, filename: string, type: string) => {
  const blob = new Blob([data], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

const downloadDvar = async (variantId: string) => {
  try {
    const response = await axiosInstance.get(`/variants/${variantId}/dvar/`, {
      responseType: "blob",
    });
    downloadFile(response.data, `${variantId}.dvar.json`, "application/json");
  } catch {
    toast.error("Failed to download DVAR");
  }
};

const downloadDsvg = async (variant: Variant) => {
  if (!variant.svgUrl) {
    toast.error("Variant has no SVG");
    return;
  }
  try {
    const response = await axiosInstance.get(variant.svgUrl, {
      baseURL: "",
      responseType: "blob",
    });
    downloadFile(response.data, `${variant.id}.dsvg.svg`, "image/svg+xml");
  } catch {
    toast.error("Failed to download DSVG");
  }
};

interface VariantRowProps {
  variant: Variant;
  onDelete: (variantId: string) => void;
  onCreateSandbox: (variant: Variant) => void;
  isCreatingSandbox: boolean;
}

const VariantRow: React.FC<VariantRowProps> = ({
  variant,
  onDelete,
  onCreateSandbox,
  isCreatingSandbox,
}) => {
  const navigate = useNavigate();
  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:h-44">
        {variant.svgUrl && (
          <div className="sm:w-44 flex-shrink-0 overflow-hidden">
            <MapPreview
              variant={variant}
              phase={variant.templatePhase}
              cover
              className="w-full aspect-video sm:aspect-auto sm:h-full"
            />
          </div>
        )}
        <div className="flex flex-col gap-2 p-4 flex-1 min-w-0 overflow-hidden">
          <div className="space-y-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold">{variant.name}</h3>
              <Badge variant={statusVariant[variant.status] ?? "outline"}>
                {statusLabel[variant.status] ?? variant.status}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              id: {variant.id}
              {variant.ownerUsername ? ` · owner: ${variant.ownerUsername}` : ""}
            </p>
            {variant.description && (
              <p className="text-sm text-muted-foreground line-clamp-2">{variant.description}</p>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => downloadDvar(variant.id)}
            >
              <Download className="size-4" /> DVAR
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => downloadDsvg(variant)}
            >
              <Download className="size-4" /> DSVG
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onCreateSandbox(variant)}
              disabled={isCreatingSandbox}
            >
              <Play className="size-4" /> Sandbox
            </Button>
            {variant.canEdit && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/variants/${variant.id}/edit`)}
                >
                  <Pencil className="size-4" /> Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => onDelete(variant.id)}
                >
                  <Trash2 className="size-4" /> Delete
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const VariantsList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: variants } = useVariantsListSuspense();
  const destroyMutation = useVariantsDestroy();
  const sandboxMutation = useSandboxGameCreate();

  const [pendingDeleteId, setPendingDeleteId] = React.useState<string | null>(
    null
  );

  const orderedVariants = React.useMemo(() => {
    const order: Record<string, number> = {
      draft: 0,
      published: 1,
      archived: 2,
    };
    return [...variants].sort((a, b) => {
      const statusDiff =
        (order[a.status] ?? 99) - (order[b.status] ?? 99);
      if (statusDiff !== 0) return statusDiff;
      return a.name.localeCompare(b.name);
    });
  }, [variants]);

  const handleDelete = async () => {
    if (!pendingDeleteId) return;
    try {
      await destroyMutation.mutateAsync({ id: pendingDeleteId });
      toast.success("Variant deleted");
      await queryClient.invalidateQueries({
        queryKey: getVariantsListQueryKey(),
      });
    } catch {
      toast.error("Failed to delete variant");
    } finally {
      setPendingDeleteId(null);
    }
  };

  const handleCreateSandbox = async (variant: Variant) => {
    try {
      const game = await sandboxMutation.mutateAsync({
        data: { name: `${variant.name} (Sandbox)`, variantId: variant.id },
      });
      toast.success("Sandbox game created");
      navigate(`/game/${game.id}`);
    } catch {
      toast.error("Failed to create sandbox game");
    }
  };

  if (orderedVariants.length === 0) {
    return (
      <Notice
        title="No variants yet"
        message="Upload a new variant draft to get started."
        icon={FilePlus}
        actions={
          <Button asChild>
            <Link to="/variants/create">Upload variant</Link>
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-3">
      {orderedVariants.map(variant => (
        <VariantRow
          key={variant.id}
          variant={variant}
          onDelete={setPendingDeleteId}
          onCreateSandbox={handleCreateSandbox}
          isCreatingSandbox={sandboxMutation.isPending}
        />
      ))}
      <AlertDialog
        open={pendingDeleteId !== null}
        onOpenChange={open => {
          if (!open) setPendingDeleteId(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this draft variant?</AlertDialogTitle>
            <AlertDialogDescription>
              Any sandbox games using this variant will also be deleted. This
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

const VariantsListSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader
        title="Variants"
        actions={
          <Button asChild size="sm">
            <Link to="/variants/create">
              <FilePlus className="size-4" /> Upload variant
            </Link>
          </Button>
        }
      />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <VariantsList />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { VariantsListSuspense as VariantsList };
