import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

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
import { SecondaryButton } from "@/components/ui/role-buttons";
import {
  ModerationReportActionKeyEnum,
  getModerationReportsListQueryKey,
  getModerationReportsRetrieveQueryKey,
  useModerationReportsReopenCreate,
} from "@/api/generated/endpoints";
import type { ModerationReportOutput } from "@/api/generated/endpoints";

interface ReportReopenProps {
  report: ModerationReportOutput;
  reportedName: string;
  reasonLabel: string;
}

const ReportReopen: React.FC<ReportReopenProps> = ({
  report,
  reportedName,
  reasonLabel,
}) => {
  const queryClient = useQueryClient();
  const reopenMutation = useModerationReportsReopenCreate();
  const [confirming, setConfirming] = useState(false);

  const available = report.actions.some(
    action =>
      action.key === ModerationReportActionKeyEnum.reopen &&
      action.blockedReason === null
  );

  if (!available) {
    return null;
  }

  const consequence =
    report.status === "approved"
      ? ` ${reportedName} loses the mark for ${reasonLabel} in this game unless another approved report gave it.`
      : "";

  const handleReopen = async () => {
    try {
      await reopenMutation.mutateAsync({ id: report.id });
    } catch {
      toast.error("Failed to reopen report");
    }
    queryClient.invalidateQueries({
      queryKey: getModerationReportsListQueryKey(),
    });
    queryClient.invalidateQueries({
      queryKey: getModerationReportsRetrieveQueryKey(report.id),
    });
  };

  return (
    <div className="flex justify-end">
      <SecondaryButton
        type="button"
        disabled={reopenMutation.isPending}
        onClick={() => setConfirming(true)}
      >
        Reopen
      </SecondaryButton>
      <AlertDialog open={confirming} onOpenChange={setConfirming}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reopen report</AlertDialogTitle>
            <AlertDialogDescription>
              {`The report goes back to Pending and is assigned to you.${consequence}`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleReopen}>Reopen</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export { ReportReopen };
