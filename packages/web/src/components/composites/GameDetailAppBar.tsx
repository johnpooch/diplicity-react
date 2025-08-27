import { useNavigate } from "react-router";
import { AppBar } from "../elements/AppBar";
import { IconButton } from "../elements/Button";
import { IconName } from "../elements/Icon";
import { createUseStyles } from "../utils/styles";
import { useResponsiveness } from "../utils/responsive";
import { Divider } from "@mui/material";

interface GameDetailAppBarProps {
  title?: string | React.ReactNode;
  onNavigateBack?: () => void;
  leftButton?: React.ReactNode;
  variant?: "primary" | "secondary";
}

const useStyles = createUseStyles<GameDetailAppBarProps>(() => ({
  root: {
    width: "100%",
    paddingLeft: 2,
    paddingRight: 2,
  },
}));

const GameDetailAppBar: React.FC<GameDetailAppBarProps> = props => {
  const navigate = useNavigate();
  const responsiveness = useResponsiveness();
  const { variant = "primary" } = props;

  const onClickBack = () => {
    if (props.onNavigateBack) {
      props.onNavigateBack();
    } else {
      navigate(-1);
    }
  };

  return (
    <>
      <AppBar
        title={props.title}
        leftButton={
          responsiveness.device === "mobile" && (
            <IconButton icon={IconName.Back} onClick={onClickBack} />
          )
        }
        rightButton={
          variant === "secondary" && responsiveness.device !== "mobile" && (
            <IconButton icon={IconName.Close} onClick={onClickBack} />
          )
        }
      />
      <Divider />
    </>
  )
};

export { GameDetailAppBar };
