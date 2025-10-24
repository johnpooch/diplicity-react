import { useNavigate } from "react-router";
import { AppBar } from "../../components/AppBar";
import { IconButton } from "../../components/Button";
import { IconName } from "../../components/Icon";
import { useResponsiveness } from "../../components/utils/responsive";
import { Divider } from "@mui/material";
import { GameMenu } from "../../components";
import { useSelectedGameContext } from "../../context";
import { GameListRead } from "../../store";

interface GameDetailAppBarProps {
  title?: string | React.ReactNode;
  onNavigateBack?: () => void;
  leftButton?: React.ReactNode;
  variant?: "primary" | "secondary";
}

const GameDetailAppBar: React.FC<GameDetailAppBarProps> = props => {
  const navigate = useNavigate();
  const responsiveness = useResponsiveness();

  const { gameRetrieveQuery } = useSelectedGameContext();

  const { variant = "primary" } = props;

  const onClickBack = () => {
    if (props.onNavigateBack) {
      props.onNavigateBack();
    } else {
      navigate(-1);
    }
  };

  const showCloseButton =
    variant === "secondary" && responsiveness.device !== "mobile";

  const handleClickGameInfo = () => {
    navigate(`/game/${gameRetrieveQuery.data?.id}/game-info`);
  };

  const handleClickPlayerInfo = () => {
    navigate(`/game/${gameRetrieveQuery.data?.id}/player-info`);
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
          showCloseButton ? (
            <IconButton icon={IconName.Close} onClick={onClickBack} />
          ) : (
            gameRetrieveQuery.data && (
              <GameMenu
                game={gameRetrieveQuery.data as GameListRead}
                onClickGameInfo={handleClickGameInfo}
                onClickPlayerInfo={handleClickPlayerInfo}
              />
            )
          )
        }
      />
      <Divider />
    </>
  );
};

export { GameDetailAppBar };
