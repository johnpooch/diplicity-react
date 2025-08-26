import { AppBar } from "../elements/AppBar";
import { createUseStyles } from "../utils/styles";

interface GameDetailAppBarProps {
  title?: string | React.ReactNode;
}

const useStyles = createUseStyles<GameDetailAppBarProps>(() => ({
  root: {
    width: "100%",
    paddingLeft: 2,
    paddingRight: 2,
  },
}));

const GameDetailAppBar: React.FC<GameDetailAppBarProps> = props => {
  const styles = useStyles(props);

  return <AppBar title={props.title} sx={styles.root} />;
};

export { GameDetailAppBar };
