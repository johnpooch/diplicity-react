import React from "react";
import { CircularProgress, Box, Typography } from "@mui/material";

type Query<TData> = {
  isLoading: boolean;
  isError: boolean;
  data?: TData;
};

type QueryContainerProps<TData> = {
  query: Query<TData>;
  onRenderLoading?: () => React.ReactNode;
  children: (data: TData) => React.ReactNode;
};

const QueryContainer = <TData,>(props: QueryContainerProps<TData>) => {
  if (props.query.isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
        padding="24px"
      >
        {props.onRenderLoading ? props.onRenderLoading() : <CircularProgress />}
      </Box>
    );
  }

  if (props.query.isError) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
      >
        <Typography variant="h6" color="error">
          An error occurred while loading data.
        </Typography>
      </Box>
    );
  }

  if (props.query.data === undefined) {
    return null;
  }

  return <>{props.children(props.query.data)}</>;
};

export { QueryContainer };
