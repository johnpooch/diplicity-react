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
import Check from "@mui/icons-material/Check";
import Map from "@mui/icons-material/Map";
import GroupAdd from "@mui/icons-material/GroupAdd";
import NoChannels from "@mui/icons-material/Forum";
import Cancel from "@mui/icons-material/Cancel";
import Close from "@mui/icons-material/Close";
import Delete from "@mui/icons-material/Delete";
import Fullscreen from "@mui/icons-material/Fullscreen";
import FullscreenExit from "@mui/icons-material/FullscreenExit";
import Lock from "@mui/icons-material/Lock";
import Clock from "@mui/icons-material/AccessTime";
import Star from "@mui/icons-material/Star";

import { SxProps, Theme } from "@mui/material";

enum IconName {
  MyGames = "my-games",
  FindGames = "find-games",
  CreateGame = "create-game",
  Add = "add",
  Profile = "profile",
  Back = "back",
  NoResults = "no-results",
  Empty = "empty",
  StartYear = "start-year",
  Failure = "failure",
  WinCondition = "win-condition",
  Players = "players",
  Author = "author",
  Menu = "menu",
  Chat = "chat",
  Orders = "orders",
  CreateOrder = "create-order",
  OrdersConfirmed = "orders-confirmed",
  OrdersNotConfirmed = "orders-not-confirmed",
  Success = "check",
  Map = "map",
  GroupAdd = "group-add",
  NoChannels = "no-channels",
  Cancel = "cancel",
  Close = "close",
  Delete = "delete",
  Fullscreen = "fullscreen",
  FullscreenExit = "fullscreen-exit",
  Lock = "lock",
  Clock = "clock",
  Star = "star",
}

const IconMap = {
  [IconName.MyGames]: Home,
  [IconName.FindGames]: Search,
  [IconName.CreateGame]: Add,
  [IconName.Add]: Add,
  [IconName.Profile]: Person,
  [IconName.Back]: ArrowBack,
  [IconName.NoResults]: NoResults,
  [IconName.Empty]: Empty,
  [IconName.StartYear]: StartYear,
  [IconName.WinCondition]: WinCondition,
  [IconName.Players]: Players,
  [IconName.Failure]: Close,
  [IconName.Author]: Author,
  [IconName.Menu]: Menu,
  [IconName.Chat]: Chat,
  [IconName.Orders]: Orders,
  [IconName.CreateOrder]: CreateOrder,
  [IconName.OrdersConfirmed]: OrdersConfirmed,
  [IconName.OrdersNotConfirmed]: OrdersNotConfirmed,
  [IconName.Success]: Check,
  [IconName.Map]: Map,
  [IconName.GroupAdd]: GroupAdd,
  [IconName.NoChannels]: NoChannels,
  [IconName.Cancel]: Cancel,
  [IconName.Close]: Close,
  [IconName.Delete]: Delete,
  [IconName.Fullscreen]: Fullscreen,
  [IconName.FullscreenExit]: FullscreenExit,
  [IconName.Lock]: Lock,
  [IconName.Clock]: Clock,
  [IconName.Star]: Star,
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
