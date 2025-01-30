import React from "react";
import { Box, Typography } from "@mui/material";

const Chat: React.FC = () => {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
      }}
    >
      <Typography variant="h4">Chat coming soon</Typography>
    </Box>
  );
};

export { Chat };
