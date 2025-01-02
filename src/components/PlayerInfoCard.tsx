import React from "react";
import {
  Avatar,
  Card,
  CardContent,
  Grid2 as Grid,
  Typography,
} from "@mui/material";
import service from "../common/store/service";

const PlayerInfoCard: React.FC<{
  member: (typeof service.endpoints.getGame.Types.ResultType)["Members"][0];
}> = (props) => {
  return (
    <Card elevation={0}>
      <CardContent>
        <Grid container spacing={1} direction="row" alignItems="center">
          <Grid container size="auto">
            <Grid>
              <Avatar
                src={props.member.User.Picture}
                alt={props.member.User.Name}
              />
            </Grid>
          </Grid>
          <Grid container size="grow" direction="column">
            <Grid container direction="row">
              <Grid>
                <Typography variant="body1">
                  {props.member.User.Name}
                </Typography>
              </Grid>
            </Grid>
          </Grid>
          <Grid container size="auto" direction="column" alignItems="flex-end">
            <Grid></Grid>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export { PlayerInfoCard };
