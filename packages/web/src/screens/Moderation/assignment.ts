import {
  ModerationReportActionBlockedReasonEnum,
  ModerationReportActionKeyEnum,
} from "@/api/generated/endpoints";
import type { ModerationReportOutput } from "@/api/generated/endpoints";

const blockedReasonOf = (
  report: ModerationReportOutput,
  key: ModerationReportActionKeyEnum
) => report.actions.find(action => action.key === key)?.blockedReason;

const assignmentLabel = (report: ModerationReportOutput) => {
  const assignBlockedReason = blockedReasonOf(
    report,
    ModerationReportActionKeyEnum.assign
  );
  if (
    assignBlockedReason ===
    ModerationReportActionBlockedReasonEnum.already_reviewed
  ) {
    return null;
  }
  if (report.assignedTo) {
    return blockedReasonOf(report, ModerationReportActionKeyEnum.unassign) ===
      null
      ? "Assigned to you"
      : `Assigned to ${report.assignedTo.name}`;
  }
  if (
    assignBlockedReason === ModerationReportActionBlockedReasonEnum.game_member
  ) {
    return "You're in this game";
  }
  return null;
};

export { assignmentLabel };
