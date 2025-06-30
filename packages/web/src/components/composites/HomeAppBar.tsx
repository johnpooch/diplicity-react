import { useNavigate } from "react-router";
import { IconName } from "../elements/Icon";
import { AppBar } from "../elements/AppBar";
import { IconButton } from "../elements/Button";

interface HomeAppBarProps {
    title: string;
}

const HomeAppBar: React.FC<HomeAppBarProps> = (props) => {
    const navigate = useNavigate();

    const onClickBack = () => {
        navigate(-1);
    };

    return (
        <AppBar
            title={props.title}
            leftButton={<IconButton icon={IconName.Back} onClick={onClickBack} />}
        />
    );
};

export { HomeAppBar };
