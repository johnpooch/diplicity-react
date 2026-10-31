import React, { Suspense } from "react";
import { Link, useSearchParams } from "react-router";
import { ArrowRight, ChevronRight, Inbox } from "lucide-react";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Notice } from "@/components/Notice";
import { ViewSelector } from "@/components/ViewSelector";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenContainer } from "@/components/ui/screen-container";
import { ScreenHeader } from "@/components/ui/screen-header";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ModerationReportsListStatus,
  useModerationReportsListSuspense,
  useReportReasonsListSuspense,
} from "@/api/generated/endpoints";
import type {
  ModerationMemberOutput,
  ModerationReportOutput,
} from "@/api/generated/endpoints";
import { formatTimeAgo } from "@/util";

const statuses = [
  { key: ModerationReportsListStatus.pending, label: "Pending" },
  { key: ModerationReportsListStatus.approved, label: "Approved" },
  { key: ModerationReportsListStatus.rejected, label: "Rejected" },
] as const;

const useStatus = (): ModerationReportsListStatus => {
  const requested = useSearchParams()[0].get("status");
  return (
    statuses.find(status => status.key === requested)?.key ??
    ModerationReportsListStatus.pending
  );
};

const memberLabel = (member: ModerationMemberOutput) => {
  const name = member.name ?? "Deleted account";
  return member.nation ? `${name} (${member.nation})` : name;
};

interface ReportRowProps {
  report: ModerationReportOutput;
  reasonLabel: string;
}

const ReportRow: React.FC<ReportRowProps> = ({ report, reasonLabel }) => (
  <li>
    <Link
      to={`/moderation/reports/${report.id}`}
      className="flex items-center gap-4 py-3 hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="flex flex-1 flex-col gap-1">
        <div className="flex items-baseline justify-between gap-4">
          <span className="font-semibold">{reasonLabel}</span>
          <span className="text-sm text-muted-foreground">
            {formatTimeAgo(report.createdAt)}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span>{memberLabel(report.reporter)}</span>
          <ArrowRight
            className="size-4 text-muted-foreground"
            aria-label="reported"
          />
          <span>{memberLabel(report.reported)}</span>
        </div>
        <span className="text-sm text-muted-foreground">
          {report.gameName} · {report.variantName}
        </span>
      </div>
      <ChevronRight className="size-4 text-muted-foreground" />
    </Link>
  </li>
);

interface ReportListProps {
  status: ModerationReportsListStatus;
}

const ReportList: React.FC<ReportListProps> = ({ status }) => {
  const { data: reports } = useModerationReportsListSuspense({ status });
  const { data: reasons } = useReportReasonsListSuspense();

  if (reports.length === 0) {
    return (
      <Notice
        icon={Inbox}
        title={`No ${status} reports`}
        message="Reports players submit will appear here."
      />
    );
  }

  return (
    <ScreenCard>
      <ScreenCardContent>
        <ul className="divide-y">
          {reports.map(report => (
            <ReportRow
              key={report.id}
              report={report}
              reasonLabel={
                reasons.find(reason => reason.key === report.reason)?.label ??
                report.reason
              }
            />
          ))}
        </ul>
      </ScreenCardContent>
    </ScreenCard>
  );
};

const ReportListSkeleton: React.FC = () => (
  <ScreenCard>
    <ScreenCardContent>
      <ul className="divide-y">
        {Array.from({ length: 4 }, (_, index) => (
          <li key={index} className="flex flex-col gap-1 py-3">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-5 w-72" />
            <Skeleton className="h-5 w-56" />
          </li>
        ))}
      </ul>
    </ScreenCardContent>
  </ScreenCard>
);

const ModerationQueueSuspense: React.FC = () => {
  const status = useStatus();
  const [, setSearchParams] = useSearchParams();

  return (
    <ScreenContainer>
      <ScreenHeader
        title="Moderation"
        actions={
          <ViewSelector
            options={statuses}
            value={status}
            defaultValue={ModerationReportsListStatus.pending}
            onChange={next =>
              setSearchParams(
                next === ModerationReportsListStatus.pending
                  ? {}
                  : { status: next }
              )
            }
            label="Choose report status"
            title="View reports"
            description="Choose which reports to show"
          />
        }
      />
      <QueryErrorBoundary key={status}>
        <Suspense fallback={<ReportListSkeleton />}>
          <ReportList status={status} />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { ModerationQueueSuspense as ModerationQueue };
