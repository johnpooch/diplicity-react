import React from "react";
import { Stack, Typography } from "@mui/material";

import UserInfo from "../components/UserInfo";

const UserPage: React.FC = () => {
  return (
    <>
      <Stack spacing={2}>
        <Typography variant="h1">Profile</Typography>
        <UserInfo />
      </Stack>
    </>
  );
};

export default UserPage;
