import React, { Suspense } from "react";
import { Link } from "react-router";
import { ChevronLeft } from "lucide-react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenContainer } from "@/components/ui/screen-container";
import { ScreenHeader } from "@/components/ui/screen-header";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useModerationReportsRetrieveSuspense,
  useReportReasonsListSuspense,
} from "@/api/generated/endpoints";
import type { ModerationMemberOutput } from "@/api/generated/endpoints";
import { useRequiredParams } from "@/hooks";
import { formatDateTime } from "@/util";

const STATUS_LABELS = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
};

const memberLabel = (member: ModerationMemberOutput) => {
  const name = member.name ?? "Deleted account";
  return member.nation ? `${name} (${member.nation})` : name;
};

const FIELDS = ["Reason", "Status", "Submitted", "Game", "Reporter", "Reported"];

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
  if (report.reviewedBy) {
    rows.push([
      `${STATUS_LABELS[report.status]} by`,
      report.reviewedBy.name,
    ]);
  }

  return (
    <div className="flex flex-col gap-4">
      <dl className="grid grid-cols-[8rem_1fr] gap-x-4 gap-y-2 text-sm">
        {rows.map(([field, value]) => (
          <React.Fragment key={field}>
            <dt className="text-muted-foreground">{field}</dt>
            <dd>{value}</dd>
          </React.Fragment>
        ))}
      </dl>
      <div className="flex flex-col gap-1">
        <h2 className="text-sm font-medium">Note</h2>
        <p className="whitespace-pre-wrap text-sm">{report.note}</p>
      </div>
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

const ModerationReportSuspense: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="Report" />
    <div>
      <Button variant="ghost" asChild>
        <Link to="/moderation">
          <ChevronLeft />
          Moderation queue
        </Link>
      </Button>
    </div>
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

export { ModerationReportSuspense as ModerationReport };
