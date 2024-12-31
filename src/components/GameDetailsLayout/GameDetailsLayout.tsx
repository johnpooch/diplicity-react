import { Outlet } from "react-router";
import PageWrapper from "../PageWrapper";
import { Fab, Stack } from "@mui/material";
import { ArrowBack as BackIcon } from "@mui/icons-material";

const GameDetailsLayout: React.FC<{
  onClickBack: () => void;
  onClickCreateOrder: () => void;
  actions: React.ReactNode[];
  navigation: React.ReactNode;
  modals: React.ReactNode[];
}> = (props) => {
  return (
    <PageWrapper>
      <Fab
        color="primary"
        aria-label="back"
        sx={{ position: "fixed", top: 16, left: 16 }}
        onClick={props.onClickBack}
      >
        <BackIcon />
      </Fab>
      <Outlet />
      <Stack
        direction="row"
        spacing={2}
        alignItems="center"
        sx={{
          position: "fixed",
          bottom: 16 + 50,
          right: 16,
        }}
      >
        {props.actions}
      </Stack>
      {props.navigation}
      {props.modals}
    </PageWrapper>
  );
};

export { GameDetailsLayout };
