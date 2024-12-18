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
                  {props.member.User.Picture}
                </Typography>
              </Grid>
              <Grid>
                <Chip label={"Consistent"} size="small" />
              </Grid>
            </Grid>
            <Grid>
              <Chip label={"Private first class"} size="small" />
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
                {8}/{6}/{4}/{2}
              </Typography>
            </Grid>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export { PlayerInfoCard };
