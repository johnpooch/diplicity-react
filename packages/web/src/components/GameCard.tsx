import React from "react";
import { Box, Button, Link, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router";
import { service } from "../store";
import { GameMenu } from "./GameMenu";
import { InteractiveMap } from "./InteractiveMap/InteractiveMap";
import { getCurrentPhase, formatDateTime } from "../util";
import { createUseStyles } from "./utils/styles";
import { MemberAvatarGroup } from "./MemberAvatarGroup";
import { Icon, IconName } from "./Icon";
import { IconButton } from "./Button";
import { useVariantById } from "../hooks";

type GameCardProps =
  (typeof service.endpoints.gamesList.Types.ResultType)[number];

const useStyles = createUseStyles<GameCardProps>(() => ({
  mainContainer: theme => ({
    borderBottom: `1px solid ${theme.palette.divider}`,
  }),
  mapWrapper: {
    maxWidth: 60,
    minWidth: 60,
    maxHeight: 54,
  },
  gameName: theme => ({
    fontSize: 15,
    lineHeight: "1.8",
    color: theme.palette.text.primary,
    "&:hover": {
      color: theme.palette.text.primary,
    },
  }),
  gameNameLink: theme => ({
    color: theme.palette.text.primary,
    "&:hover": {
      color: theme.palette.text.primary,
    },
    "&:after": {
      borderBottomColor: theme.palette.text.primary,
    },
  }),
  lockIcon: {
    fontSize: 12,
    opacity: 0.6,
  },
  phaseInfo: theme => ({
    color: theme.palette.text.primary,
  }),
  memberButton: {
    padding: 0,
    width: "fit-content",
    justifyContent: "flex-start",
  },
  memberContainer: {
    paddingBottom: "4px",
    paddingLeft: "6px",
  },
}));

const GameCard: React.FC<GameCardProps> = game => {
  const navigate = useNavigate();
  const styles = useStyles(game);
  const currentPhase = getCurrentPhase(game.phases);
  const variant = useVariantById(game.variantId);

  const [joinGame, joinGameMutation] =
    service.endpoints.gameJoinCreate.useMutation();

  const handleClickJoinGame = async () => {
    await joinGame({ gameId: game.id, member: {} });
    navigate(`/game-info/${game.id}`);
  };

  const handleClickGameInfo = () => {
    navigate(`/game-info/${game.id}`);
  };

  const handleClickPlayerInfo = () => {
    navigate(`/player-info/${game.id}`);
  };

  const handleClickGame = () => {
    if (game.status === "active") {
      navigate(`/game/${game.id}`);
    } else {
      navigate(`/game-info/${game.id}`);
    }
  };

  if (!variant) {
    return null;
  }

  return (
    <Stack p={1} gap={1} direction="row" sx={styles.mainContainer}>
      <Stack gap={1} flex={1}>
        <Stack direction="row" gap={1}>
          <Stack sx={styles.mapWrapper}>
            <Link
              onClick={handleClickGame}
              style={{ width: "100%", height: "100%" }}
            >
              <Box sx={{ width: "100%", height: "100%" }}>
                <InteractiveMap
                  style={{ borderRadius: 5, width: "100%", height: "100%" }}
                  variant={variant}
                  phase={currentPhase}
                  orders={[]}
                  selected={[]}
                />
              </Box>
            </Link>
          </Stack>
          <Stack>
            <Stack direction="row" gap={1} alignItems="center">
              <Link
                onClick={handleClickGame}
                underline="hover"
                sx={styles.gameNameLink}
              >
                <Typography variant="body2" sx={styles.gameName}>
                  {game.name}
                </Typography>
              </Link>
            </Stack>
            <Stack direction="row" gap={1} alignItems="center">
              {game.private && (
                <Icon name={IconName.Lock} sx={styles.lockIcon} />
              )}
              <Typography variant="caption">
                {variant.name} •{" "}
                {game.movementPhaseDuration
                  ? game.movementPhaseDuration
                  : "Resolve when ready"}
              </Typography>
            </Stack>
          </Stack>
        </Stack>
        {game.status === "active" && (
          <Stack>
            <Typography variant="caption" sx={styles.phaseInfo}>
              {currentPhase?.season} {currentPhase?.year} • {currentPhase?.type}{" "}
              {currentPhase?.scheduledResolution
                ? `• Resolves ${formatDateTime(currentPhase?.scheduledResolution)}`
                : ""}
            </Typography>
          </Stack>
        )}
        {!game.sandbox && (
          <Button onClick={handleClickPlayerInfo} sx={styles.memberButton}>
            <Stack direction="row" gap={1} sx={styles.memberContainer}>
              <MemberAvatarGroup members={game.members} variant={variant.id} />
            </Stack>
          </Button>
        )}
      </Stack>
      <Stack justifyContent="space-between">
        <GameMenu
          game={game}
          onClickGameInfo={handleClickGameInfo}
          onClickPlayerInfo={handleClickPlayerInfo}
        />
        {game.canJoin && (
          <IconButton
            icon={IconName.Join}
            color="primary"
            disabled={joinGameMutation.isLoading}
            onClick={handleClickJoinGame}
          />
        )}
      </Stack>
    </Stack>
  );
};

export { GameCard };
