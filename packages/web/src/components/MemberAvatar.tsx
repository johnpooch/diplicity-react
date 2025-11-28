import { Avatar, AvatarProps, Badge, Box } from "@mui/material";

import { Flags } from "../assets/flags";
import { MemberRead } from "../store/service";
import { Icon, IconName } from "./Icon";

const AVATAR_SIZE = {
  small: 24,
  medium: 32,
};

const BADGE_SIZE = {
  small: 16,
  medium: 24,
};

const BORDER_SIZE = {
  small: 1,
  medium: 2,
};

const TROPHY_SIZE = {
  small: 16,
  medium: 20,
};

type MemberAvatarProps = Pick<AvatarProps, "key"> & {
  size: "small" | "medium";
  variant: string;
  member: Pick<MemberRead, "picture" | "nation">;
  isWinner?: boolean;
};

const MemberAvatar: React.FC<MemberAvatarProps> = ({
  variant,
  member,
  size,
  isWinner = false,
  ...rest
}) => {
  const avatarSize = AVATAR_SIZE[size];
  const badgeSize = BADGE_SIZE[size];
  const borderSize = BORDER_SIZE[size];
  const trophySize = TROPHY_SIZE[size];

  const mainAvatar = (
    <Avatar
      {...rest}
      src={member.picture ?? undefined}
      sx={{ width: avatarSize, height: avatarSize }}
    />
  );

  const nationFlag =
    Flags[variant as keyof typeof Flags]?.[
      member.nation?.toLowerCase() as keyof (typeof Flags)[keyof typeof Flags]
    ];

  // Create trophy badge for winners
  const trophyBadge = isWinner ? (
    <Box
      sx={{
        bgcolor: "warning.main",
        borderRadius: "50%",
        width: trophySize,
        height: trophySize,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: `${borderSize}px solid white`,
      }}
    >
      <Icon
        name={IconName.Trophy}
        sx={{ fontSize: 12, color: "warning.contrastText" }}
      />
    </Box>
  ) : null;

  // Create nation flag badge
  const nationBadge = member.nation ? (
    <Avatar
      src={nationFlag}
      sx={{
        width: badgeSize,
        height: badgeSize,
        border: `${borderSize}px solid white`,
      }}
    />
  ) : null;

  // Build avatar with nested badges
  let avatar = mainAvatar;

  // Add nation badge at bottom-right if present
  if (nationBadge) {
    avatar = (
      <Badge
        overlap="circular"
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        badgeContent={nationBadge}
      >
        {avatar}
      </Badge>
    );
  }

  // Add trophy badge at top-right if present (only when player has won)
  if (trophyBadge) {
    avatar = (
      <Badge
        overlap="circular"
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        badgeContent={trophyBadge}
      >
        {avatar}
      </Badge>
    );
  }

  return avatar;
};

export { MemberAvatar };
