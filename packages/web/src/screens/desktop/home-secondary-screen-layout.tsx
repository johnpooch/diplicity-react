import { Stack, Divider } from "@mui/material";
import { NavigateFunction, Outlet, useNavigate } from "react-router";
import { AppBar } from "../../components/elements/AppBar";
import { IconButton } from "../../components/elements/Button";
import { IconName } from "../../components/elements/Icon";

type HomeSecondaryScreenLayoutProps = {
  title: string;
  onNavigateBack: (navigate: NavigateFunction) => void;
  secondaryAction?: React.ReactNode;
};

const HomeSecondaryScreenLayout: React.FC<HomeSecondaryScreenLayoutProps> = (
  props
) => {
  const navigate = useNavigate();
  return (
    <Stack sx={styles.root}>
      <AppBar title={props.title} leftButton={
        <IconButton
          icon={IconName.Back}
          onClick={() => props.onNavigateBack(navigate)}
        />}
        rightButton={props.secondaryAction}
      />
      <Divider />
      <Outlet />
    </Stack>
  );
};

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
  backButtonTitleContainer: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    width: "100%",
    gap: 1,
  },
};

export { HomeSecondaryScreenLayout };
