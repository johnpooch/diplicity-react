import React from "react";
import { CircularProgress, Box, Typography } from "@mui/material";

type Query<TData> = {
  isLoading: boolean;
  isError: boolean;
  data?: TData;
};

type QueryContainerProps<TData> = {
  query: Query<TData>;
  children: (data: TData) => React.ReactNode;
};

const QueryContainer = <TData,>({
  query,
  children,
}: QueryContainerProps<TData>) => {
  if (query.isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="80vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (query.isError) {
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

  if (query.data === undefined) {
    return null;
  }

  return <>{children(query.data)}</>;
};

export { QueryContainer };
