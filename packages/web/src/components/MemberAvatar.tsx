import React from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Flags } from "../assets/flags";
import { cn } from "../lib/utils";
import { Member } from "../api/generated/endpoints";

type MemberAvatarProps = {
  member: Pick<Member, "picture" | "nation">;
  variant: string;
  size?: "small" | "medium";
  isWinner?: boolean;
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

const MemberAvatar: React.FC<MemberAvatarProps> = ({
  member,
  variant,
  size = "medium",
  isWinner = false,
}) => {
  const config = SIZE_CONFIG[size];
  const nationFlag =
    Flags[variant as keyof typeof Flags]?.[
      member.nation?.toLowerCase() as keyof (typeof Flags)[keyof typeof Flags]
    ];

  return (
    <div className="relative w-fit">
      <Avatar
        className={cn(
          config.avatar,
          isWinner
            ? `ring-offset-background ${config.ring} ring-yellow-500`
            : `${config.border} border-white`
        )}
      >
        <AvatarImage src={member.picture ?? undefined} />
        <AvatarFallback>{member.nation?.toUpperCase()[0]}</AvatarFallback>
      </Avatar>

      {member.nation && nationFlag && (
        <span
          className={cn(
            "absolute -right-1.5 -bottom-1.5 inline-flex items-center justify-center rounded-full bg-white z-10",
            config.badge
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

export { MemberAvatar };
