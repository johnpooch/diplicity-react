import React from "react";
import { Divider, Grid2 as Grid, Typography } from "@mui/material";
import { useGameInfoQuery } from "../common/hooks/useGameInfo";
import {
  Map as VariantIcon,
  TimerOutlined as DeadlinesIcon,
  CheckBoxOutlined as CommitmentIcon,
  MilitaryTech as RankIcon,
  Language as LanguageIcon,
  People as PlayersIcon,
  Flag as WinConditionIcon,
  CalendarToday as StartYearIcon,
  Person as AuthorIcon,
} from "@mui/icons-material";

const BlankIcon: React.FC = () => <div style={{ width: 20, height: 20 }}></div>;

const TableRow: React.FC<{
  label: string;
  value: string;
  icon: React.ReactElement;
}> = ({ label, value, icon }) => {
  return (
    <Grid container justifyContent="space-between">
      <Grid container alignItems="center" gap={1}>
        <Grid>{icon}</Grid>
        <Grid>
          <Typography variant="body2">{label}</Typography>
        </Grid>
      </Grid>
      <Grid>
        <Typography>{value}</Typography>
      </Grid>
    </Grid>
  );
};

const GameInfo: React.FC<{
  gameId: string;
  useGameInfoQuery: typeof useGameInfoQuery;
}> = (props) => {
  const query = props.useGameInfoQuery(props.gameId);

  if (query.isSuccess) {
    return (
      <Grid container direction="column">
        <Grid
          container
          direction="column"
          style={{ paddingTop: 8, paddingBottom: 8 }}
        >
          <Grid>
            <Typography>Game settings</Typography>
          </Grid>
          <Grid>
            <TableRow
              label="Variant"
              value={query.data.variant.name}
              icon={<VariantIcon fontSize="small" />}
            />
            <TableRow
              label="Phase Deadlines"
              value={""}
              icon={<DeadlinesIcon fontSize="small" />}
            />
            <TableRow
              label="Movement"
              value={query.data.movementPhaseDuration}
              icon={<BlankIcon />}
            />
            <TableRow
              label="Non-Movement"
              value={query.data.nonMovementPhaseDuration}
              icon={<BlankIcon />}
            />
          </Grid>
        </Grid>
        <Divider />
        <Grid
          container
          direction="column"
          style={{ paddingTop: 8, paddingBottom: 8 }}
        >
          <Grid>
            <Typography>Player settings</Typography>
          </Grid>
          <Grid>
            {query.data.minCommitment && (
              <TableRow
                label="Min. commitment"
                value={query.data.minCommitment}
                icon={<CommitmentIcon fontSize="small" />}
              />
            )}
            {(query.data.minRank || query.data.maxRank) && (
              <TableRow
                label="Rank"
                value={""}
                icon={<RankIcon fontSize="small" />}
              />
            )}
            {query.data.minRank && (
              <TableRow
                label="Min"
                value={query.data.minRank}
                icon={<BlankIcon />}
              />
            )}
            {query.data.maxRank && (
              <TableRow
                label="Max"
                value={query.data.maxRank}
                icon={<BlankIcon />}
              />
            )}
            {query.data.language && (
              <TableRow
                label="Language"
                value={query.data.language}
                icon={<LanguageIcon fontSize="small" />}
              />
            )}
          </Grid>
        </Grid>
        <Divider />
        <Grid
          container
          direction="column"
          style={{ paddingTop: 8, paddingBottom: 8 }}
        >
          <Grid>
            <Typography>Variant details</Typography>
          </Grid>
          <Grid>
            <TableRow
              label="Players"
              value={query.data.variant.numPlayers.toString()}
              icon={<PlayersIcon fontSize="small" />}
            />
            <TableRow
              label="Win condition"
              value={query.data.variant.winCondition}
              icon={<WinConditionIcon fontSize="small" />}
            />
            <TableRow
              label="Start year"
              value={query.data.variant.startYear.toString()}
              icon={<StartYearIcon fontSize="small" />}
            />
            <TableRow
              label="Original author"
              value={query.data.variant.author}
              icon={<AuthorIcon fontSize="small" />}
            />
          </Grid>
        </Grid>
      </Grid>
    );
  }
};

export { GameInfo };
