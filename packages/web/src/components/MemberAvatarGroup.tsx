import React from "react";
import { AvatarGroup, Button } from "@mui/material";
import { MemberRead, VictoryRead } from "../store/service";
import { MemberAvatar } from "./MemberAvatar";
import { Icon, IconName } from "./Icon";

type MemberAvatarGroupProps = {
  members: MemberRead[];
  variant: string;
  victory?: VictoryRead | null;
  max?: number;
  size?: "small" | "medium";
  onClick?: () => void;
};

const MemberAvatarGroup: React.FC<MemberAvatarGroupProps> = ({
  members,
  variant,
  victory,
  max = 7,
  size = "small",
  onClick,
}) => {
  const avatarSize = size === "small" ? 24 : 32;
  const iconSize = size === "small" ? 16 : 20;

  const winnerIds = victory?.members?.map((m) => m.id) || [];

  const avatarGroup = (
    <AvatarGroup
      total={members.length}
      max={max}
      slotProps={{
        surplus: {
          sx: { width: `${avatarSize}px`, height: `${avatarSize}px` },
        },
      }}
      renderSurplus={() => (
        <Icon sx={{ width: iconSize, height: iconSize }} name={IconName.Add} />
      )}
    >
      {members.map(member => (
        <MemberAvatar
          key={member.id}
          member={member}
          variant={variant}
          size={size}
          isWinner={winnerIds.includes(member.id)}
        />
      ))}
    </AvatarGroup>
  );

  if (onClick) {
    return (
      <Button
        sx={{
          justifyContent: "flex-start",
          width: "fit-content",
          padding: "8px 0px 8px 0px",
        }}
        onClick={onClick}
      >
        {avatarGroup}
      </Button>
    );
  }

  return avatarGroup;
};

export { MemberAvatarGroup };
