import { useNavigate } from "react-router";
import { AppBar } from "../../AppBar";
import { IconButton } from "../../Button";
import { IconName } from "../../Icon";
import { useResponsiveness } from "../../utils/responsive";
import { Divider } from "@mui/material";

interface GameDetailAppBarProps {
  title?: string | React.ReactNode;
  onNavigateBack?: () => void;
  leftButton?: React.ReactNode;
  variant?: "primary" | "secondary";
}

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
