import React from "react";

import type { DrawProposal } from "@/api/generated/endpoints";
import { Badge } from "@/components/ui/badge";

export const getDrawProposalNotificationCount = (
  proposals: readonly DrawProposal[] | undefined
) =>
  proposals?.filter(
    proposal =>
      proposal.status === "pending" &&
      proposal.myVote !== null &&
      proposal.myVote.accepted === null
  ).length ?? 0;

export const DrawProposalNotificationBadge: React.FC<{ count: number }> = ({
  count,
}) => {
  if (count === 0) return null;

  return (
    <Badge
      variant="destructive"
      className="absolute -right-1 -top-1 h-4 w-4 justify-center p-0 text-[10px]"
    >
      {count}
    </Badge>
  );
};
