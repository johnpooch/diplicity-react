import React, { Suspense, useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { useAuth } from "@/auth";
import { useUserDeleteDestroy } from "@/api/generated/endpoints";

const DeleteAccount: React.FC = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const deleteMutation = useUserDeleteDestroy();
  const [confirmText, setConfirmText] = useState("");

  const isConfirmed = confirmText.trim().toLowerCase() === "delete";

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync();
      logout();
    } catch {
      toast.error("Failed to delete account");
    }
  };

  return (
    <ScreenCard>
      <ScreenCardContent className="space-y-4">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-destructive">
            This action is irreversible
          </h2>
          <p className="text-sm text-muted-foreground">
            Deleting your account will:
          </p>
          <ul className="text-sm text-muted-foreground list-disc pl-4 space-y-1">
            <li>Remove you from all games</li>
            <li>Permanently delete your account and profile</li>
          </ul>
        </div>

        <div className="space-y-2">
          <p className="text-sm">
            Type <span className="font-mono font-semibold">delete</span> to
            confirm:
          </p>
          <Input
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="delete"
            autoComplete="off"
          />
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => navigate("/profile")}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            disabled={!isConfirmed || deleteMutation.isPending}
            onClick={handleDelete}
            className="flex-1"
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete Account"}
          </Button>
        </div>
      </ScreenCardContent>
    </ScreenCard>
  );
};

const DeleteAccountSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Delete Account" />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <DeleteAccount />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { DeleteAccountSuspense as DeleteAccount };
