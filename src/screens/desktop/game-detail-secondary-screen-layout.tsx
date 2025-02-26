import { Stack, Typography, IconButton, Divider } from "@mui/material";
import { NavigateFunction, Outlet, useNavigate } from "react-router";
import { ArrowBack as BackIcon } from "@mui/icons-material";
import { useGameDetailContext } from "../../context";
import { useChannel } from "../../components/channel/channel";
import { useChannelContext } from "../../context/channel-context";

const styles: Styles = {
  root: {
    flexGrow: 1,
    height: "100vh",
    overflow: "hidden",
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

type GameDetailSecondaryScreenLayoutProps = {
  title: string | React.ReactNode;
  onNavigateBack: (navigate: NavigateFunction, gameId: string) => void;
};

const GameDetailSecondaryScreenLayout: React.FC<
  GameDetailSecondaryScreenLayoutProps
> = (props) => {
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();
  
  // Wrap channel-related hooks in try-catch to make them optional
  let channelTitle;
  try {
    const { channelName } = useChannelContext();
    const { query } = useChannel();
    if (channelName) {
      channelTitle = query.data?.displayName;
    }
  } catch {
    // Context not available, that's fine
  }
  
  const title = channelTitle ?? props.title;

  return (
    <Stack sx={styles.root}>
      <Stack sx={styles.topBar}>
        <IconButton onClick={() => props.onNavigateBack(navigate, gameId)}>
          <BackIcon />
        </IconButton>
        {typeof title === "string" ? (
          <Typography variant="h1">{title}</Typography>
        ) : (
          title
        )}
      </Stack>
      <Divider />
      <Outlet />
    </Stack>
  );
};

export { GameDetailSecondaryScreenLayout };
