import React from "react";
import {
  Avatar,
  Card,
  CardContent,
  Chip,
  Grid2 as Grid,
  IconButton,
  Typography,
} from "@mui/material";
import { MoreHoriz as MenuIcon } from "@mui/icons-material";
import { Display } from "../common/display";

const PlayerInfoCard: React.FC<Display.GameMember> = (props) => {
  return (
    <Card elevation={0}>
      <CardContent>
        <Grid container spacing={1} direction="row" alignItems="center">
          <Grid container size="auto">
            <Grid>
              <Avatar src={props.src} alt={props.username} />
            </Grid>
          </Grid>
          <Grid container size="grow" direction="column">
            <Grid container direction="row">
              <Grid>
                <Typography variant="body1">{props.username}</Typography>
              </Grid>
              <Grid>
                <Chip label={props.stats.consistency} size="small" />
              </Grid>
            </Grid>
            <Grid>
              <Chip label={props.stats.rank} size="small" />
            </Grid>
          </Grid>
          <Grid container size="auto" direction="column" alignItems="flex-end">
            <Grid>
              <IconButton onClick={() => alert("Clicked")}>
                <MenuIcon />
              </IconButton>
            </Grid>
            <Grid>
              <Typography variant="body2">
                {props.stats.numPlayed}/{props.stats.numWon}/
                {props.stats.numDrawn}/{props.stats.numAbandoned}
              </Typography>
            </Grid>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export { PlayerInfoCard };
