import React from "react";
import { ShieldAlert, ShieldCheck, ShieldHalf, Sprout } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

export const COMMITMENT_TIERS: Record<
  string,
  {
    label: string;
    icon: React.ReactNode;
    badgeClassName?: string;
    badgeVariant: "default" | "secondary" | "destructive";
    explanation: string;
  }
> = {
  high: {
    label: "High",
    icon: <ShieldCheck className="size-3" />,
    badgeClassName: "bg-green-600",
    badgeVariant: "default",
    explanation:
      "This player has consistently submitted orders in their recent games.",
  },
  medium: {
    label: "Medium",
    icon: <ShieldHalf className="size-3" />,
    badgeVariant: "secondary",
    explanation:
      "This player has missed some order deadlines in their recent games.",
  },
  low: {
    label: "Low",
    icon: <ShieldAlert className="size-3" />,
    badgeVariant: "destructive",
    explanation:
      "This player has missed many order deadlines in their recent games.",
  },
  undefined: {
    label: "New",
    icon: <Sprout className="size-3" />,
    badgeVariant: "secondary",
    explanation:
      "This player hasn't played enough rated phases to have a commitment rating yet.",
  },
};

interface CommitmentBadgeProps {
  commitment: string;
}

export const CommitmentBadge: React.FC<CommitmentBadgeProps> = ({
  commitment,
}) => {
  const tier = COMMITMENT_TIERS[commitment];
  if (!tier) return null;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button type="button" aria-label={`Commitment: ${tier.label}`}>
          <Badge
            variant={tier.badgeVariant}
            className={`gap-1 cursor-pointer ${tier.badgeClassName ?? ""}`}
          >
            {tier.icon}
            {tier.label}
          </Badge>
        </button>
      </PopoverTrigger>
      <PopoverContent className="text-sm">
        <p className="font-medium mb-1">{tier.label} commitment</p>
        <p className="text-muted-foreground">{tier.explanation}</p>
      </PopoverContent>
    </Popover>
  );
};
