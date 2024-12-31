import { Outlet } from "react-router";
import PageWrapper from "../PageWrapper";
import { Fab } from "@mui/material";
import {
  ArrowBack as BackIcon,
  Add as CreateOrderIcon,
} from "@mui/icons-material";

const GameDetailsLayout: React.FC<{
  onClickBack: () => void;
  onClickCreateOrder: () => void;
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
      <Fab
        color="primary"
        aria-label="create-order"
        sx={{ position: "fixed", bottom: 16 + 50, right: 16 }}
        onClick={props.onClickCreateOrder}
      >
        <CreateOrderIcon />
      </Fab>
      {props.navigation}
      {props.modals}
    </PageWrapper>
  );
};

export { GameDetailsLayout };
