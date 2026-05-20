import React, { Suspense, useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { ArrowLeft } from "lucide-react";

import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenContainer } from "@/components/ui/screen-container";
import { ScreenHeader } from "@/components/ui/screen-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";

import {
  useVariantsCreate,
  useVariantsUpdate,
  useVariantsRetrieveSuspense,
  getVariantsListQueryKey,
  VariantWrite,
} from "@/api/generated/endpoints";
import { useQueryClient } from "@tanstack/react-query";

interface VariantUploadFormProps {
  mode: "create" | "edit";
  variantId?: string;
  submitLabel: string;
  warning?: React.ReactNode;
  onSubmit: (files: { dvar: File; dsvg: File }) => Promise<void>;
  isSubmitting: boolean;
}

interface ServerError {
  dvar?: unknown;
  dsvg?: unknown;
  detail?: string;
  [key: string]: unknown;
}

const renderErrors = (errors: ServerError | null) => {
  if (!errors) return null;
  const entries: Array<{ field: string; messages: string[] }> = [];

  const collect = (field: string, value: unknown) => {
    if (value == null) return;
    if (typeof value === "string") {
      entries.push({ field, messages: [value] });
      return;
    }
    if (Array.isArray(value)) {
      const messages = value.map(item => {
        if (typeof item === "string") return item;
        if (typeof item === "object" && item !== null) {
          const obj = item as { code?: string; message?: string; path?: string };
          const parts = [obj.message ?? JSON.stringify(item)];
          if (obj.code) parts.unshift(`[${obj.code}]`);
          if (obj.path) parts.push(`(at ${obj.path})`);
          return parts.join(" ");
        }
        return String(item);
      });
      entries.push({ field, messages });
      return;
    }
    if (typeof value === "object") {
      entries.push({ field, messages: [JSON.stringify(value)] });
    }
  };

  for (const [field, value] of Object.entries(errors)) {
    collect(field, value);
  }

  if (entries.length === 0) return null;

  return (
    <Alert variant="destructive">
      <AlertTitle>Upload failed</AlertTitle>
      <AlertDescription>
        <ul className="list-disc pl-4 space-y-1">
          {entries.flatMap(({ field, messages }) =>
            messages.map((message, index) => (
              <li key={`${field}-${index}`}>
                <span className="font-semibold">{field}:</span> {message}
              </li>
            ))
          )}
        </ul>
      </AlertDescription>
    </Alert>
  );
};

const VariantUploadForm: React.FC<VariantUploadFormProps> = ({
  submitLabel,
  warning,
  onSubmit,
  isSubmitting,
}) => {
  const [dvar, setDvar] = useState<File | null>(null);
  const [dsvg, setDsvg] = useState<File | null>(null);
  const [errors, setErrors] = useState<ServerError | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!dvar || !dsvg) {
      setErrors({ detail: "Choose both a DVAR and a DSVG file." });
      return;
    }
    setErrors(null);
    try {
      await onSubmit({ dvar, dsvg });
    } catch (error) {
      const axiosError = error as AxiosError<ServerError>;
      const data = axiosError.response?.data ?? {
        detail: axiosError.message ?? "Unknown error",
      };
      setErrors(data);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {warning}
      <div className="space-y-2">
        <Label htmlFor="dvar">DVAR file (JSON)</Label>
        <Input
          id="dvar"
          type="file"
          accept=".json,.dvar,application/json"
          onChange={event => setDvar(event.target.files?.[0] ?? null)}
          disabled={isSubmitting}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="dsvg">DSVG file (SVG)</Label>
        <Input
          id="dsvg"
          type="file"
          accept=".svg,image/svg+xml"
          onChange={event => setDsvg(event.target.files?.[0] ?? null)}
          disabled={isSubmitting}
        />
      </div>
      {renderErrors(errors)}
      <div className="flex gap-2">
        <Button type="submit" disabled={isSubmitting || !dvar || !dsvg}>
          {isSubmitting ? "Uploading…" : submitLabel}
        </Button>
      </div>
    </form>
  );
};

const VariantCreate: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const createMutation = useVariantsCreate();

  const handleSubmit = async ({ dvar, dsvg }: { dvar: File; dsvg: File }) => {
    await createMutation.mutateAsync({
      data: {
        dvar: dvar as unknown as VariantWrite["dvar"],
        dsvg: dsvg as unknown as VariantWrite["dsvg"],
      },
    });
    toast.success("Draft variant uploaded");
    await queryClient.invalidateQueries({
      queryKey: getVariantsListQueryKey(),
    });
    navigate("/variants");
  };

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" onClick={() => navigate("/variants")}>
        <ArrowLeft className="size-4" /> Back to variants
      </Button>
      <VariantUploadForm
        mode="create"
        submitLabel="Upload draft"
        onSubmit={handleSubmit}
        isSubmitting={createMutation.isPending}
      />
    </div>
  );
};

const VariantEdit: React.FC<{ variantId: string }> = ({ variantId }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: variant } = useVariantsRetrieveSuspense(variantId);
  const updateMutation = useVariantsUpdate();

  const handleSubmit = async ({ dvar, dsvg }: { dvar: File; dsvg: File }) => {
    await updateMutation.mutateAsync({
      id: variantId,
      data: {
        dvar: dvar as unknown as VariantWrite["dvar"],
        dsvg: dsvg as unknown as VariantWrite["dsvg"],
      },
    });
    toast.success(`Updated draft variant '${variantId}'`);
    await queryClient.invalidateQueries({
      queryKey: getVariantsListQueryKey(),
    });
    navigate("/variants");
  };

  if (!variant.canEdit) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Cannot edit this variant</AlertTitle>
        <AlertDescription>
          Only the owner of a draft variant can edit it. Published and archived
          variants are immutable.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" onClick={() => navigate("/variants")}>
        <ArrowLeft className="size-4" /> Back to variants
      </Button>
      <VariantUploadForm
        mode="edit"
        variantId={variantId}
        submitLabel="Replace files"
        warning={
          <Alert>
            <AlertTitle>This replaces the variant wholesale.</AlertTitle>
            <AlertDescription>
              Uploading new files for '{variant.name}' deletes any sandbox games
              using it.
            </AlertDescription>
          </Alert>
        }
        onSubmit={handleSubmit}
        isSubmitting={updateMutation.isPending}
      />
    </div>
  );
};

const VariantCreateSuspense: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="Upload variant" />
    <ScreenCard>
      <ScreenCardContent>
        <QueryErrorBoundary>
          <Suspense fallback={<div></div>}>
            <VariantCreate />
          </Suspense>
        </QueryErrorBoundary>
      </ScreenCardContent>
    </ScreenCard>
  </ScreenContainer>
);

interface VariantEditSuspenseProps {
  variantId: string;
}

const VariantEditSuspense: React.FC<VariantEditSuspenseProps> = ({
  variantId,
}) => (
  <ScreenContainer>
    <ScreenHeader title="Edit variant" />
    <ScreenCard>
      <ScreenCardContent>
        <QueryErrorBoundary>
          <Suspense fallback={<div></div>}>
            <VariantEdit variantId={variantId} />
          </Suspense>
        </QueryErrorBoundary>
      </ScreenCardContent>
    </ScreenCard>
  </ScreenContainer>
);

export {
  VariantCreateSuspense as VariantCreate,
  VariantEditSuspense as VariantEdit,
};
