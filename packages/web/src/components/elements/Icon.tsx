import ArrowBack from "@mui/icons-material/ArrowBack";
import Home from "@mui/icons-material/Home";
import Search from "@mui/icons-material/Search";
import Add from "@mui/icons-material/Add";
import CreateOrder from "@mui/icons-material/Add";
import Person from "@mui/icons-material/Person";
import Author from "@mui/icons-material/Person";
import NoResults from "@mui/icons-material/SearchOff";
import Empty from "@mui/icons-material/InboxOutlined";
import StartYear from "@mui/icons-material/CalendarToday";
import WinCondition from "@mui/icons-material/Flag";
import Players from "@mui/icons-material/People";
import Menu from "@mui/icons-material/MoreHoriz";
import Chat from "@mui/icons-material/Chat";
import Orders from "@mui/icons-material/Gavel";
import OrdersConfirmed from "@mui/icons-material/CheckBox";
import OrdersNotConfirmed from "@mui/icons-material/CheckBoxOutlineBlank";

import { SxProps, Theme } from "@mui/material";

enum IconName {
  MyGames = "my-games",
  FindGames = "find-games",
  CreateGame = "create-game",
  Profile = "profile",
  Back = "back",
  NoResults = "no-results",
  Empty = "empty",
  StartYear = "start-year",
  WinCondition = "win-condition",
  Players = "players",
  Author = "author",
  Menu = "menu",
  Chat = "chat",
  Orders = "orders",
  CreateOrder = "create-order",
  OrdersConfirmed = "orders-confirmed",
  OrdersNotConfirmed = "orders-not-confirmed",
}

const IconMap = {
  [IconName.MyGames]: Home,
  [IconName.FindGames]: Search,
  [IconName.CreateGame]: Add,
  [IconName.Profile]: Person,
  [IconName.Back]: ArrowBack,
  [IconName.NoResults]: NoResults,
  [IconName.Empty]: Empty,
  [IconName.StartYear]: StartYear,
  [IconName.WinCondition]: WinCondition,
  [IconName.Players]: Players,
  [IconName.Author]: Author,
  [IconName.Menu]: Menu,
  [IconName.Chat]: Chat,
  [IconName.Orders]: Orders,
  [IconName.CreateOrder]: CreateOrder,
  [IconName.OrdersConfirmed]: OrdersConfirmed,
  [IconName.OrdersNotConfirmed]: OrdersNotConfirmed,
};

interface IconProps {
  name: IconName;
  sx?: SxProps<Theme>;
}

const Icon: React.FC<IconProps> = ({ name, ...rest }) => {
  const IconComponent = IconMap[name];

  return <IconComponent {...rest} />;
};

export { Icon, IconName };
