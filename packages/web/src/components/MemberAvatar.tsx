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
  medium: 24,
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

  // Determine badge content based on winner status and nation
  const badgeContent = isWinner ? (
    <Box
      sx={{
        bgcolor: "warning.main",
        borderRadius: "50%",
        width: badgeSize,
        height: badgeSize,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: `${borderSize}px solid white`,
      }}
    >
      <Icon
        name={IconName.Trophy}
        sx={{ fontSize: trophySize, color: "warning.contrastText" }}
      />
    </Box>
  ) : member.nation ? (
    <Avatar
      src={nationFlag}
      sx={{
        width: badgeSize,
        height: badgeSize,
        border: `${borderSize}px solid white`,
      }}
    />
  ) : null;

  // If no badge content, just return the avatar
  if (!badgeContent) {
    return mainAvatar;
  }

  // Otherwise, wrap it with the Badge
  return (
    <Badge
      overlap="circular"
      anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      badgeContent={badgeContent}
    >
      {mainAvatar}
    </Badge>
  );
};

export { MemberAvatar };
