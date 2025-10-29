import React from "react";
import { Box, Button, Link, Skeleton, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router";
import { service } from "../store";
import { GameMenu } from "./GameMenu";
import { InteractiveMap } from "./InteractiveMap/InteractiveMap";
import { formatDateTime } from "../util";
import { createUseStyles } from "./utils/styles";
import { MemberAvatarGroup } from "./MemberAvatarGroup";
import { Icon, IconName } from "./Icon";
import { IconButton } from "./Button";
import { useVariantById } from "../hooks";

type GameCardProps = {
  game?: (typeof service.endpoints.gamesList.Types.ResultType)[number];
};

const getCurrentPhaseId = (phaseIds: number[]): number | undefined => {
  if (!phaseIds || phaseIds.length === 0) return undefined;
  // Phases are ordered by ordinal, so the last one is the current phase
  return phaseIds[phaseIds.length - 1];
};

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

const GameCard: React.FC<GameCardProps> = props => {
  const navigate = useNavigate();
  const styles = useStyles(props);
  const currentPhaseId = getCurrentPhaseId(props.game?.phases ?? []);
  const variant = useVariantById(props.game?.variantId ?? "");

  const currentPhaseQuery = service.endpoints.gamePhaseRetrieve.useQuery(
    {
      gameId: props.game?.id ?? "",
      phaseId: currentPhaseId || 0,
    },
    {
      skip: !currentPhaseId,
    }
  );

  const [joinGame, joinGameMutation] =
    service.endpoints.gameJoinCreate.useMutation();

  const handleClickJoinGame = async () => {
    if (!props.game) return;
    await joinGame({ gameId: props.game.id, member: {} });
    navigate(`/game-info/${props.game.id}`);
  };

  const handleClickGameInfo = () => {
    if (!props.game) return;
    navigate(`/game-info/${props.game.id}`);
  };

  const handleClickPlayerInfo = () => {
    if (!props.game) return;
    navigate(`/player-info/${props.game.id}`);
  };

  const handleClickGame = () => {
    if (!props.game) return;
    if (props.game.status === "active") {
      navigate(`/game/${props.game.id}`);
    } else {
      navigate(`/game-info/${props.game.id}`);
    }
  };

  return (
    <Stack p={1} gap={1} direction="row" sx={styles.mainContainer}>
      <Stack gap={1} flex={1}>
        <Stack direction="row" gap={1}>
          <Stack sx={styles.mapWrapper}>
            {props.game ? (
              <Link
                onClick={handleClickGame}
                style={{ width: "100%", height: "100%" }}
              >
                <Box sx={{ width: "100%", height: "100%" }}>
                  {currentPhaseQuery.data && variant ? (
                    <InteractiveMap
                      style={{ borderRadius: 5, width: "100%", height: "100%" }}
                      variant={variant}
                      phase={currentPhaseQuery.data}
                      orders={[]}
                      selected={[]}
                    />
                  ) : (
                    <Skeleton variant="rectangular" width={60} height={52} />
                  )}
                </Box>
              </Link>
            ) : (
              <Skeleton variant="rectangular" width={60} height={52} />
            )}
          </Stack>
          <Stack>
            {props.game ? (
              <>
                <Stack direction="row" gap={1} alignItems="center">
                  <Link
                    onClick={handleClickGame}
                    underline="hover"
                    sx={styles.gameNameLink}
                  >
                    <Typography variant="body2" sx={styles.gameName}>
                      {props.game.name}
                    </Typography>
                  </Link>
                </Stack>
                <Stack direction="row" gap={1} alignItems="center">
                  {props.game.private && (
                    <Icon name={IconName.Lock} sx={styles.lockIcon} />
                  )}
                  {variant ? (
                    <Typography variant="caption">
                      {variant.name} •{" "}
                      {props.game.movementPhaseDuration
                        ? props.game.movementPhaseDuration
                        : "Resolve when ready"}
                    </Typography>
                  ) : (
                    <Skeleton variant="text" width={80} height={18} />
                  )}
                </Stack>
              </>
            ) : (
              <>
                <Stack direction="row" gap={1} alignItems="center">
                  <Skeleton variant="text" width={200} height={27} />
                </Stack>
                <Stack direction="row" gap={1} alignItems="center">
                  <Skeleton variant="text" width={80} height={18} />
                </Stack>
              </>
            )}
          </Stack>
        </Stack>
        <Stack>
          {currentPhaseQuery.data ? (
            <Typography variant="caption" sx={styles.phaseInfo}>
              {currentPhaseQuery.data?.season} {currentPhaseQuery.data?.year} •{" "}
              {currentPhaseQuery.data?.type}{" "}
              {currentPhaseQuery.data?.scheduledResolution
                ? `• Resolves ${formatDateTime(currentPhaseQuery.data?.scheduledResolution)}`
                : ""}
            </Typography>
          ) : (
            <Skeleton variant="text" width={300} height={18} />
          )}
        </Stack>
        {props.game && variant && !props.game.sandbox ? (
          <Button onClick={handleClickPlayerInfo} sx={styles.memberButton}>
            <Stack direction="row" gap={1} sx={styles.memberContainer}>
              <MemberAvatarGroup
                members={props.game.members}
                variant={variant.id}
              />
            </Stack>
          </Button>
        ) : !props.game ? (
          <Skeleton variant="rectangular" width={150} height={32} />
        ) : null}
      </Stack>
      <Stack justifyContent="space-between">
        {props.game ? (
          <>
            <GameMenu
              game={props.game}
              onClickGameInfo={handleClickGameInfo}
              onClickPlayerInfo={handleClickPlayerInfo}
            />
            {props.game.canJoin && (
              <IconButton
                icon={IconName.Join}
                color="primary"
                disabled={joinGameMutation.isLoading}
                onClick={handleClickJoinGame}
              />
            )}
          </>
        ) : (
          <Skeleton variant="circular" width={24} height={24} />
        )}
      </Stack>
    </Stack>
  );
};

export { GameCard };
