import React from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Flags } from "../assets/flags";
import { Plus } from "lucide-react";
import { cn } from "../lib/utils";
import { GameRetrieveVictory, Member } from "../api/generated/endpoints";

type MemberAvatarGroupProps = {
  members: readonly Member[];
  variant: string;
  victory?: GameRetrieveVictory;
  max?: number;
  size?: "small" | "medium";
  onClick?: () => void;
};

const SIZE_CONFIG = {
  small: {
    avatar: "h-6 w-6",
    badge: "size-3",
    border: "border",
    ring: "ring-2",
  },
  medium: {
    avatar: "h-8 w-8",
    badge: "size-4",
    border: "border-2",
    ring: "ring-2",
  },
};

const MemberAvatar: React.FC<{
  member: Member;
  variant: string;
  size: "small" | "medium";
  isWinner: boolean;
}> = ({ member, variant, size, isWinner }) => {
  const config = SIZE_CONFIG[size];
  const nationFlag =
    Flags[variant as keyof typeof Flags]?.[
      member.nation?.toLowerCase() as keyof (typeof Flags)[keyof typeof Flags]
    ];

  return (
    <div className="relative w-fit">
      <Avatar
        className={`${config.avatar} ${isWinner ? `ring-offset-background ${config.ring} ring-yellow-500` : `${config.border} border-white`}`}
      >
        <AvatarImage src={member.picture ?? undefined} />
        <AvatarFallback>{member.nation?.toUpperCase()[0]}</AvatarFallback>
      </Avatar>

      {member.nation && nationFlag && (
        <span
          className={cn(
            // FIX: Added z-10 to ensure the flag is rendered above other Avatars
            "absolute -right-1.5 -bottom-1.5 inline-flex items-center justify-center rounded-full bg-white",
            config.badge,
            "z-10" // <-- **CRITICAL FIX: Renders the flag above overlapping elements**
          )}
        >
          <img
            src={nationFlag}
            alt={member.nation}
            className="h-full w-full rounded-full object-cover"
          />
        </span>
      )}
    </div>
  );
};

const MemberAvatarGroup: React.FC<MemberAvatarGroupProps> = ({
  members,
  variant,
  victory,
  max = 7,
  size = "medium",
  onClick,
}) => {
  const config = SIZE_CONFIG[size];
  const winnerIds = victory?.members?.map(m => m.id) || [];
  const displayMembers = members.slice(0, max);
  const remainingCount = members.length - max;

  const content = (
    <div className="flex -space-x-2">
      {displayMembers.map(member => (
        <MemberAvatar
          key={member.id}
          member={member}
          variant={variant}
          size={size}
          isWinner={winnerIds.includes(member.id)}
        />
      ))}
      {remainingCount > 0 && (
        <div
          className={`${config.avatar} rounded-full bg-muted border-2 border-background flex items-center justify-center`}
        >
          <Plus className="h-full w-full p-1" />
        </div>
      )}
    </div>
  );

  if (onClick) {
    return (
      <button
        onClick={onClick}
        className="p-0 hover:opacity-80 transition-opacity"
      >
        {content}
      </button>
    );
  }

  return content;
};

export { MemberAvatarGroup };
