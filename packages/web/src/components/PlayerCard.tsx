import React from "react";
import { Chip, Skeleton, Stack, Typography } from "@mui/material";
import { MemberAvatar } from "./MemberAvatar";
import { PhaseRead, service, VictoryRead } from "../store";
import { createUseStyles } from "./utils/styles";
import { Icon, IconName } from "./Icon";

type Member =
  (typeof service.endpoints.gameRetrieve.Types.ResultType)["members"][number];

type PlayerCardProps = {
  member: Member;
  variant: string;
  phase: PhaseRead | undefined;
  victory?: VictoryRead | null;
};

const useStyles = createUseStyles<PlayerCardProps>(() => ({
  mainContainer: theme => ({
    borderBottom: `1px solid ${theme.palette.divider}`,
  }),
  username: () => ({
    fontSize: 15,
    lineHeight: "1.8",
  }),
  starIcon: {
    fontSize: 12,
    opacity: 0.6,
  },
}));

const PlayerCard: React.FC<PlayerCardProps> = props => {
  const styles = useStyles(props);

  const supplyCenterCount = props.phase?.supplyCenters.filter(
    sc => sc.nation.name === props.member.nation
  ).length;

  const isWinner = props.victory?.members?.some((m) => m.id === props.member.id);

  return (
    <Stack p={1} gap={1} direction="row" sx={styles.mainContainer}>
      <Stack gap={1} flex={1}>
        <Stack direction="row" gap={2}>
          <Stack justifyContent="center">
            <MemberAvatar
              member={props.member}
              variant={props.variant}
              size="medium"
              isWinner={isWinner}
            />
          </Stack>
          <Stack flex={1}>
            <Stack
              direction="row"
              alignItems="flex-start"
              flexDirection="column"
            >
              <Stack direction="row" gap={1} alignItems="center">
                <Typography variant="body2" sx={styles.username}>
                  {props.member.name}
                </Typography>
                {isWinner && (
                  <Chip
                    icon={<Icon name={IconName.Trophy} />}
                    label={props.victory?.type === "solo" ? "Winner" : "Draw"}
                    color="warning"
                    size="small"
                  />
                )}
              </Stack>
              {props.member.nation && (
                <Stack direction="row" gap={1} alignItems="center">
                  <Typography variant="caption">
                    {props.member.nation}
                  </Typography>
                  <Typography variant="caption">•</Typography>
                  <Stack direction="row" gap={0.5} alignItems="center">
                    <Icon name={IconName.Star} sx={styles.starIcon} />
                    {supplyCenterCount ? (
                      <Typography variant="caption">
                        {supplyCenterCount}
                      </Typography>
                    ) : (
                      <Skeleton variant="text" width={10} height={10} />
                    )}
                  </Stack>
                </Stack>
              )}
            </Stack>
          </Stack>
        </Stack>
      </Stack>
    </Stack>
  );
};

export { PlayerCard };
