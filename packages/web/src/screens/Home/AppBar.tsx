import { useNavigate } from "react-router";
import { IconName } from "../../components/Icon";
import { AppBar } from "../../components/AppBar";
import { IconButton } from "../../components/Button";

interface HomeAppBarProps {
  title: string;
  onNavigateBack?: () => void;
  leftButton?: React.ReactNode;
  rightButton?: React.ReactNode;
}

const HomeAppBar: React.FC<HomeAppBarProps> = props => {
  const navigate = useNavigate();

  const onClickBack = () => {
    if (props.onNavigateBack) {
      props.onNavigateBack();
    } else {
      navigate(-1);
    }
  };

  console.log(props.rightButton);

  return (
    <AppBar
      title={props.title}
      leftButton={
        props.leftButton ? (
          props.leftButton
        ) : (
          <IconButton icon={IconName.Back} onClick={onClickBack} />
        )
      }
      rightButton={props.rightButton}
    />
  );
};

export { HomeAppBar };
