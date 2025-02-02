import React from "react";
import { Box } from "@mui/material";
import { ChannelList } from "../../components";

const ChannelListMobile: React.FC = () => {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
      }}
    >
      <ChannelList />
    </Box>
  );
};

export { ChannelListMobile };
