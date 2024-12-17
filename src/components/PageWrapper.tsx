import React from "react";
import { Box } from "@mui/material";

const PageWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        width: "100%",
      }}
    >
      <Box
        sx={{
          maxWidth: 630 + 320,
          width: "100%",
          margin: "0 auto",
        }}
      >
        {children}
      </Box>
    </div>
  );
};

export default PageWrapper;
