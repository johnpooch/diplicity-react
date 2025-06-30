import ArrowBack from "@mui/icons-material/ArrowBack";
import Home from "@mui/icons-material/Home";
import Search from "@mui/icons-material/Search";
import Add from "@mui/icons-material/Add";
import Person from "@mui/icons-material/Person";
import NoResults from "@mui/icons-material/SearchOff";
import Empty from "@mui/icons-material/InboxOutlined";
import { SxProps, Theme } from "@mui/material";

enum IconName {
    MyGames = "my-games",
    FindGames = "find-games",
    CreateGame = "create-game",
    Profile = "profile",
    Back = "back",
    NoResults = "no-results",
    Empty = "empty",
}

const IconMap = {
    [IconName.MyGames]: Home,
    [IconName.FindGames]: Search,
    [IconName.CreateGame]: Add,
    [IconName.Profile]: Person,
    [IconName.Back]: ArrowBack,
    [IconName.NoResults]: NoResults,
    [IconName.Empty]: Empty,
}

interface IconProps {
    name: IconName,
    sx?: SxProps<Theme>;
}

const Icon: React.FC<IconProps> = ({ name, ...rest }) => {
    const IconComponent = IconMap[name];

    return (
        <IconComponent {...rest} />
    )
}

export { Icon, IconName };