import React, { Suspense } from "react";
import { useLocation, useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenContainer } from "@/components/ui/screen-container";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ModerationReportActionKeyEnum,
  getModerationReportsListQueryKey,
  getModerationReportsRetrieveQueryKey,
  useModerationReportsAssignCreate,
  useModerationReportsRetrieveSuspense,
  useModerationReportsUnassignCreate,
  useReportReasonsListSuspense,
} from "@/api/generated/endpoints";
import type {
  ModerationMemberOutput,
  ModerationReportOutput,
} from "@/api/generated/endpoints";
import { useRequiredParams } from "@/hooks";
import { formatDateTime } from "@/util";
import { GameDetailAppBar } from "../GameDetail/AppBar";
import { assignmentLabel } from "./assignment";

const STATUS_LABELS = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
};

const memberLabel = (member: ModerationMemberOutput) => {
  const name = member.name ?? "Deleted account";
  return member.nation ? `${name} (${member.nation})` : name;
};

const FIELDS = [
  "Reason",
  "Status",
  "Submitted",
  "Game",
  "Reporter",
  "Reported",
];

const ACTIONS = {
  [ModerationReportActionKeyEnum.assign]: {
    label: "Assign to me",
    failure: "Failed to assign report",
  },
  [ModerationReportActionKeyEnum.unassign]: {
    label: "Unassign",
    failure: "Failed to unassign report",
  },
};

interface ReportAssignmentProps {
  report: ModerationReportOutput;
}

const ReportAssignment: React.FC<ReportAssignmentProps> = ({ report }) => {
  const queryClient = useQueryClient();
  const assignMutation = useModerationReportsAssignCreate();
  const unassignMutation = useModerationReportsUnassignCreate();
  const label = assignmentLabel(report);
  const available = report.actions.filter(
    action => action.blockedReason === null
  );

  if (label === null && available.length === 0) {
    return null;
  }

  const handleAction = async (key: ModerationReportActionKeyEnum) => {
    const mutation =
      key === ModerationReportActionKeyEnum.assign
        ? assignMutation
        : unassignMutation;
    try {
      await mutation.mutateAsync({ id: report.id });
    } catch {
      toast.error(ACTIONS[key].failure);
    }
    queryClient.invalidateQueries({
      queryKey: getModerationReportsListQueryKey(),
    });
    queryClient.invalidateQueries({
      queryKey: getModerationReportsRetrieveQueryKey(report.id),
    });
  };

  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <span className="text-muted-foreground">{label}</span>
      {available.map(action => (
        <Button
          key={action.key}
          size="sm"
          variant="outline"
          disabled={assignMutation.isPending || unassignMutation.isPending}
          onClick={() => handleAction(action.key)}
        >
          {ACTIONS[action.key].label}
        </Button>
      ))}
    </div>
  );
};

const ModerationReport: React.FC = () => {
  const { reportId } = useRequiredParams<{ reportId: string }>();
  const { data: report } = useModerationReportsRetrieveSuspense(
    Number(reportId)
  );
  const { data: reasons } = useReportReasonsListSuspense();

  const values = [
    reasons.find(reason => reason.key === report.reason)?.label ??
      report.reason,
    STATUS_LABELS[report.status],
    formatDateTime(report.createdAt),
    `${report.gameName} · ${report.variantName}`,
    memberLabel(report.reporter),
    memberLabel(report.reported),
  ];
  const rows = FIELDS.map((field, index) => [field, values[index]]);
  if (report.review) {
    rows.push([
      `${STATUS_LABELS[report.status]} by`,
      report.review.reviewedBy.name,
    ]);
  }

  return (
    <div className="flex flex-col gap-4">
      <ReportAssignment report={report} />
      <dl className="grid grid-cols-[8rem_1fr] gap-x-4 gap-y-2 text-sm">
        {rows.map(([field, value]) => (
          <React.Fragment key={field}>
            <dt className="text-muted-foreground">{field}</dt>
            <dd>{value}</dd>
          </React.Fragment>
        ))}
      </dl>
      <div className="flex flex-col gap-1">
        <h2 className="text-sm font-medium">Reporter's note</h2>
        <p className="whitespace-pre-wrap text-sm">{report.note}</p>
      </div>
      {report.review?.note && (
        <div className="flex flex-col gap-1">
          <h2 className="text-sm font-medium">Moderator's note</h2>
          <p className="whitespace-pre-wrap text-sm">{report.review.note}</p>
        </div>
      )}
    </div>
  );
};

const ModerationReportSkeleton: React.FC = () => (
  <div className="flex flex-col gap-4">
    <div className="grid grid-cols-[8rem_1fr] gap-x-4 gap-y-2">
      {FIELDS.map(field => (
        <React.Fragment key={field}>
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-5 w-56" />
        </React.Fragment>
      ))}
    </div>
    <div className="flex flex-col gap-1">
      <Skeleton className="h-5 w-12" />
      <Skeleton className="h-5 w-full" />
    </div>
  </div>
);

const ModerationReportSuspense: React.FC = () => {
  const navigate = useNavigate();
  const { state } = useLocation();
  const queueSearch =
    typeof state?.queueSearch === "string" ? state.queueSearch : "";

  return (
    <ScreenContainer>
      <GameDetailAppBar
        title="Report"
        variant="secondary"
        onNavigateBack={() => navigate(`/moderation${queueSearch}`)}
      />
      <ScreenCard>
        <ScreenCardContent>
          <QueryErrorBoundary>
            <Suspense fallback={<ModerationReportSkeleton />}>
              <ModerationReport />
            </Suspense>
          </QueryErrorBoundary>
        </ScreenCardContent>
      </ScreenCard>
    </ScreenContainer>
  );
};

export { ModerationReportSuspense as ModerationReport };
