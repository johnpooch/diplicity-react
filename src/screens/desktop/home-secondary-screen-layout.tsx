import { Stack, Typography, IconButton, Divider } from "@mui/material";
import { NavigateFunction, Outlet, useNavigate } from "react-router";
import { ArrowBack as BackIcon } from "@mui/icons-material";

const styles: Styles = {
  root: {
    flexGrow: 1,
  },
  topBar: {
    minHeight: 56,
    flexDirection: "row",
    alignItems: "center",
    padding: 1,
    gap: 1,
    "& h1": {
      margin: 0,
    },
  },
};

type HomeSecondaryScreenLayoutProps = {
  title: string | React.ReactNode;
  onNavigateBack: (navigate: NavigateFunction) => void;
};

const HomeSecondaryScreenLayout: React.FC<HomeSecondaryScreenLayoutProps> = (
  props,
) => {
  const navigate = useNavigate();
  return (
    <Stack sx={styles.root}>
      <Stack sx={styles.topBar}>
        <IconButton onClick={() => props.onNavigateBack(navigate)}>
          <BackIcon />
        </IconButton>
        {typeof props.title === "string" ? (
          <Typography variant="h1">{props.title}</Typography>
        ) : (
          props.title
        )}
      </Stack>
      <Divider />
      <Outlet />
    </Stack>
  );
};

export { HomeSecondaryScreenLayout };
