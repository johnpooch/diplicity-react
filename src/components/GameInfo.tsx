import React from "react";
import { Divider, Grid2 as Grid, Typography } from "@mui/material";
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
import service from "../common/store/service";

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
  getGameQuery?: typeof service.endpoints.getGame.useQuery;
  listVariantsQuery?: typeof service.endpoints.listVariants.useQuery;
}> = (props) => {
  const getGameQuery = props.getGameQuery
    ? props.getGameQuery(props.gameId)
    : service.endpoints.getGame.useQuery(props.gameId);

  const listVariantsQuery = props.listVariantsQuery
    ? props.listVariantsQuery(undefined)
    : service.endpoints.listVariants.useQuery(undefined);

  if (listVariantsQuery.isSuccess && getGameQuery.isSuccess) {
    const game = getGameQuery.data;
    const variant = listVariantsQuery.data.find(
      (variant) => variant.Name === game.Variant
    );

    if (!variant) throw new Error("Variant not found");

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
              value={variant.Name}
              icon={<VariantIcon fontSize="small" />}
            />
            <TableRow
              label="Phase Deadlines"
              value={""}
              icon={<DeadlinesIcon fontSize="small" />}
            />
            {game.PhaseLengthMinutes && (
              <TableRow
                label="Movement"
                value={game.PhaseLengthMinutes}
                icon={<BlankIcon />}
              />
            )}
            {game.NonMovementPhaseLengthMinutes && (
              <TableRow
                label="Non-Movement"
                value={game.NonMovementPhaseLengthMinutes}
                icon={<BlankIcon />}
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
            <Typography>Player settings</Typography>
          </Grid>
          <Grid>
            {game.MinReliability && (
              <TableRow
                label="Min. reliability"
                value={game.MinReliability}
                icon={<CommitmentIcon fontSize="small" />}
              />
            )}
            {(game.MinRating || game.MaxRating) && (
              <TableRow
                label="Rank"
                value={""}
                icon={<RankIcon fontSize="small" />}
              />
            )}
            {game.MinRating && (
              <TableRow
                label="Min"
                value={game.MinRating}
                icon={<BlankIcon />}
              />
            )}
            {game.MaxRating && (
              <TableRow
                label="Max"
                value={game.MaxRating}
                icon={<BlankIcon />}
              />
            )}
            {game.ChatLanguageISO639_1 && (
              <TableRow
                label="Chat language"
                value={game.ChatLanguageISO639_1}
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
              value={variant.Nations.length.toString()}
              icon={<PlayersIcon fontSize="small" />}
            />
            <TableRow
              label="Win condition"
              value={variant.Rules}
              icon={<WinConditionIcon fontSize="small" />}
            />
            <TableRow
              label="Start year"
              value={variant.Start.Year.toString()}
              icon={<StartYearIcon fontSize="small" />}
            />
            <TableRow
              label="Original author"
              value={variant.CreatedBy}
              icon={<AuthorIcon fontSize="small" />}
            />
          </Grid>
        </Grid>
      </Grid>
    );
  }
};

export { GameInfo };
