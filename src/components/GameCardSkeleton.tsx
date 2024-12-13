import React from "react";
import { Card, CardContent, Grid2 as Grid, Skeleton, Box } from "@mui/material";

const GameCardSkeleton: React.FC = () => {
  return (
    <Card>
      <CardContent>
        <Grid container spacing={2}>
          {/* Top */}
          <Grid container size={12} alignItems="center">
            <Grid size="auto">
              <Skeleton variant="circular" width={24} height={24} />
            </Grid>
            <Grid size="grow">
              <Skeleton variant="text" width="60%" height={32} />
            </Grid>
            <Grid size="auto">
              <Skeleton variant="circular" width={24} height={24} />
            </Grid>
          </Grid>
          {/* Middle */}
          <Grid container size={12}>
            <Grid size="grow" alignItems="center">
              <Grid>
                <Skeleton variant="text" width="40%" height={20} />
              </Grid>
            </Grid>
            <Grid
              container
              size="grow"
              justifyContent="flex-end"
              alignItems="center"
            >
              <Skeleton variant="rectangular" width={100} height={20} />
              <Skeleton variant="text" width="20%" height={20} />
            </Grid>
          </Grid>
          {/* Bottom */}
          <Grid container size={12} alignItems="center">
            <Grid>
              <Box display="flex">
                <Skeleton variant="circular" width={32} height={32} />
                <Skeleton
                  variant="circular"
                  width={32}
                  height={32}
                  sx={{ ml: -1 }}
                />
                <Skeleton
                  variant="circular"
                  width={32}
                  height={32}
                  sx={{ ml: -1 }}
                />
              </Box>
            </Grid>
            <Grid container justifyContent="flex-end" size="grow">
              <Skeleton variant="text" width="40%" height={20} />
            </Grid>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default GameCardSkeleton;
