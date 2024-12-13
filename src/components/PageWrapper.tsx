import React from "react";
import { Box, useTheme } from "@mui/material";

const PageWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = useTheme();
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        padding: "16px",
        width: "100%",
        backgroundColor: theme.palette.background.default,
      }}
    >
      <Box
        sx={{
          maxWidth: 630 + 320,
          width: "100%",
          margin: "0 auto",
          padding: "16px",
        }}
      >
        {children}
      </Box>
    </div>
  );
};

export default PageWrapper;
