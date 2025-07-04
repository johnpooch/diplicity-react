import { useNavigate } from "react-router";
import { IconName } from "../elements/Icon";
import { AppBar } from "../elements/AppBar";
import { IconButton } from "../elements/Button";

interface HomeAppBarProps {
  title: string;
  onNavigateBack?: () => void;
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

  return (
    <AppBar
      title={props.title}
      leftButton={<IconButton icon={IconName.Back} onClick={onClickBack} />}
    />
  );
};

export { HomeAppBar };
