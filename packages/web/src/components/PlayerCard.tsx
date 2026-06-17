import React from "react";
import { Shield, Star, Trophy, Swords, Gavel } from "lucide-react";
import { Link } from "react-router";

import { CivilDisorderBadge } from "@/components/CivilDisorderBadge";
import { NationFlag, findNationFlagUrl, findNationColor } from "@/components/NationFlag";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Member, Variant } from "@/api/generated/endpoints";
import { cn } from "@/lib/utils";

interface PlayerCardProps {
  member: Member;
  variant: Variant;
  gameId: string;
  phaseId?: string;
  supplyCenterCount?: number;
  unitCount?: number;
  remainingOrders?: number;
  showOrdersCount?: boolean;
  nmrExtensionsAllowed?: number;
  isWinner?: boolean;
  victoryType?: string;
  className?: string;
}

const PlayerCard: React.FC<PlayerCardProps> = ({
  member,
  variant,
  gameId,
  phaseId,
  supplyCenterCount,
  unitCount,
  remainingOrders,
  showOrdersCount,
  nmrExtensionsAllowed,
  isWinner,
  victoryType,
  className,
}) => (
  <div className={cn("flex items-start gap-3", className)}>
    {member.nation && (
      <NationFlag
        flagUrl={findNationFlagUrl(variant.nations, member.nation)}
        alt={member.nation}
        size="lg"
        color={findNationColor(variant.nations, member.nation)}
      />
    )}
    <div className="flex-1 min-w-0">
      {member.nation && (
        <div className="font-semibold text-sm">{member.nation}</div>
      )}
      <div className="flex items-center gap-2 flex-wrap">
        {member.userId ? (
          <Link
            to={
              phaseId
                ? `/game/${gameId}/phase/${phaseId}/player/${member.userId}`
                : `/player/${member.userId}`
            }
            className="text-sm text-primary underline-offset-4 hover:underline"
          >
            {member.name}
          </Link>
        ) : (
          <span className="text-sm">{member.name}</span>
        )}
        {member.isCurrentUser && (
          <Badge variant="secondary" className="text-xs">
            you
          </Badge>
        )}
        {member.isGameCreator && (
          <Badge variant="secondary" className="gap-1 text-xs">
            <Shield className="size-3" />
            Game Creator
          </Badge>
        )}
        {isWinner && (
          <Badge variant="default" className="gap-1 text-xs">
            <Trophy className="size-3" />
            {victoryType === "solo" ? "Winner" : "Draw"}
          </Badge>
        )}
        {member.civilDisorder && <CivilDisorderBadge />}
      </div>
      <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="inline-flex items-center gap-1">
              <Star className="size-3" />
              {supplyCenterCount !== undefined ? (
                <span>{supplyCenterCount}</span>
              ) : (
                <Skeleton className="h-3 w-4" />
              )}
            </span>
          </TooltipTrigger>
          <TooltipContent>Supply centres</TooltipContent>
        </Tooltip>
        <span>•</span>
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="inline-flex items-center gap-1">
              <Swords className="size-3" />
              {unitCount !== undefined ? (
                <span>{unitCount}</span>
              ) : (
                <Skeleton className="h-3 w-4" />
              )}
            </span>
          </TooltipTrigger>
          <TooltipContent>Units</TooltipContent>
        </Tooltip>
        {showOrdersCount && (
          <>
            <span>•</span>
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="inline-flex items-center gap-1">
                  <Gavel className="size-3" />
                  {remainingOrders !== undefined ? (
                    <span>{remainingOrders}</span>
                  ) : (
                    <Skeleton className="h-3 w-4" />
                  )}
                </span>
              </TooltipTrigger>
              <TooltipContent>Orders remaining</TooltipContent>
            </Tooltip>
          </>
        )}
        {nmrExtensionsAllowed !== undefined && nmrExtensionsAllowed > 0 && (
          <>
            <span>•</span>
            <span>{member.nmrExtensionsRemaining} ext. remaining</span>
          </>
        )}
      </div>
    </div>
  </div>
);

export { PlayerCard };
