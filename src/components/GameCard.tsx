import React, { useState } from "react";
import {
  MoreHoriz,
  Share as ShareIcon,
  Info as InfoIcon,
  People as PeopleIcon,
  Lock as LockIcon,
  Add as JoinIcon,
  TimerOutlined as PhaseTimeRemainingIcon,
  Map as VariantIcon,
} from "@mui/icons-material";
import {
  Card,
  CardContent,
  Grid2 as Grid,
  IconButton,
  Typography,
  Menu,
  MenuItem,
  useTheme,
  Divider,
  Stack,
  Button,
  Chip,
  Avatar,
} from "@mui/material";
import StatusChip from "./StatusChip";
import PlayerAvatar from "./PlayerAvatar";
import { useGlobalModal } from "../GlobalModalContext";
import service from "../common/store/service";

const MAX_AVATARS = 7;

const orderStatusLabelMap: Record<
  React.ComponentProps<typeof StatusChip>["status"],
  string
> = {
  missed: "Orders missed",
  unconfirmed: "Orders not confirmed",
  pending: "Orders pending",
  confirmed: "Orders confirmed",
};

type GameCallback = (id: string) => void;

type GameCallbacks = {
  onClickPlayerInfo: GameCallback;
  onClickGameInfo: GameCallback;
  onClickShare: GameCallback;
  onClickJoin: GameCallback;
  onClickLeave: GameCallback;
  onClickViewGame: GameCallback;
};

const GameCard: React.FC<
  {
    game: (typeof service.endpoints.listGames.Types.ResultType)[0];
    user: typeof service.endpoints.getRoot.Types.ResultType;
  } & GameCallbacks
> = (props) => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const { openModal } = useGlobalModal();

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const withMenuClose = (callback: () => void) => () => {
    handleMenuClose();
    callback();
  };

  const displayedUsers = props.game.Members.slice(0, MAX_AVATARS);
  const remainingUsersCount = props.game.Members.length - displayedUsers.length;

  const userMember = props.game.Members.find(
    (member) => member.User.Id === props.user.Id
  );

  const userCanJoin = props.game.Links.some((link) => link.Rel === "join");
  const userCanLeave = props.game.Links.some((link) => link.Rel === "leave");

  return (
    <Card elevation={0}>
      <CardContent>
        <Stack>
          <Grid container spacing={2}>
            {/* Top */}
            <Grid container size={12} alignItems="center">
              {userMember && userMember.Nation && (
                <Grid size="auto">
                  <Avatar
                    style={{ width: 24, height: 24 }}
                    src={`https://diplicity-engine.appspot.com/Variant/${props.game.Variant}/Flags/${userMember.Nation}.svg`}
                  />
                </Grid>
              )}
              <Grid size="grow">
                <Stack direction="row" alignItems="center" gap={1}>
                  <Typography variant="h4" style={{ fontSize: "18px" }}>
                    {props.game.Desc}
                  </Typography>
                  {props.game.Private && (
                    <LockIcon style={{ width: 16, height: 16 }} />
                  )}
                  <StatusChip
                    status={"confirmed"}
                    label={orderStatusLabelMap["confirmed"]}
                  />
                </Stack>
              </Grid>
              <Grid size="auto">
                <IconButton aria-label="menu" onClick={handleMenuClick}>
                  <MoreHoriz />
                </IconButton>
                <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                  <MenuItem
                    onClick={withMenuClose(() =>
                      openModal("gameInfo", props.game.ID)
                    )}
                  >
                    <InfoIcon sx={{ marginRight: 1 }} />
                    Game info
                  </MenuItem>
                  <MenuItem
                    onClick={withMenuClose(() =>
                      openModal("playerInfo", props.game.ID)
                    )}
                  >
                    <PeopleIcon sx={{ marginRight: 1 }} />
                    Player info
                  </MenuItem>
                  <Divider />
                  {userCanJoin && (
                    <MenuItem
                      onClick={withMenuClose(() =>
                        props.onClickJoin(props.game.ID)
                      )}
                    >
                      <JoinIcon sx={{ marginRight: 1 }} />
                      Join
                    </MenuItem>
                  )}
                  {props.game.Started && (
                    <MenuItem
                      onClick={withMenuClose(() =>
                        props.onClickViewGame(props.game.ID)
                      )}
                    >
                      <VariantIcon sx={{ marginRight: 1 }} />
                      View
                    </MenuItem>
                  )}
                  {userCanLeave && (
                    <MenuItem
                      onClick={withMenuClose(() =>
                        props.onClickLeave(props.game.ID)
                      )}
                    >
                      Leave
                    </MenuItem>
                  )}
                  <MenuItem
                    onClick={withMenuClose(() =>
                      props.onClickShare(props.game.ID)
                    )}
                  >
                    <ShareIcon sx={{ marginRight: 1 }} />
                    Share
                  </MenuItem>
                </Menu>
              </Grid>
            </Grid>
            {/* Middle */}
            <Grid container size={12}>
              <Grid size="grow" alignItems="center">
                <Stack direction="row" gap={1}>
                  <Typography
                    variant="body2"
                    style={{
                      color: theme.palette.text.secondary,
                      fontSize: "15px",
                    }}
                  >
                    {props.game.Variant}
                  </Typography>
                  <Typography
                    variant="body2"
                    style={{
                      color: theme.palette.text.secondary,
                      fontSize: "15px",
                    }}
                  >
                    {props.game.PhaseLengthMinutes}
                  </Typography>
                </Stack>
              </Grid>
              <Grid
                container
                size="grow"
                justifyContent="flex-end"
                alignItems="center"
              >
                {props.game.NewestPhaseMeta && (
                  <>
                    <Typography
                      variant="body2"
                      style={{
                        color: theme.palette.text.secondary,
                        fontSize: "15px",
                      }}
                    >
                      {`${props.game.NewestPhaseMeta.Season} ${props.game.NewestPhaseMeta.Year}, ${props.game.NewestPhaseMeta.Type}`}
                    </Typography>
                    {props.game.Started && !props.game.Finished && (
                      <Chip
                        icon={
                          <PhaseTimeRemainingIcon
                            style={{ width: 16, height: 16 }}
                          />
                        }
                        label={props.game.NewestPhaseMeta.NextDeadlineIn}
                      />
                    )}
                  </>
                )}
              </Grid>
            </Grid>
            {/* Bottom */}
            <Grid container size={12} alignItems="center">
              <Grid>
                <Stack
                  direction="row"
                  spacing={-1}
                  alignItems="center"
                  onClick={() => openModal("playerInfo", props.game.ID)}
                  sx={{ cursor: "pointer" }}
                >
                  {displayedUsers.map((member, index) => (
                    <PlayerAvatar key={index} username={member.User.Name} />
                  ))}
                  {remainingUsersCount > 0 && (
                    <Typography
                      variant="body2"
                      sx={{ paddingLeft: 1, alignSelf: "center" }}
                    >
                      +{remainingUsersCount}
                    </Typography>
                  )}
                </Stack>
              </Grid>
              <Grid container justifyContent="flex-end" size="grow">
                {userCanJoin && (
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => props.onClickJoin(props.game.ID)}
                    size="small"
                  >
                    Join
                  </Button>
                )}
              </Grid>
            </Grid>
          </Grid>
        </Stack>
      </CardContent>
    </Card>
  );
};

export { GameCard };
export type { GameCallbacks };
