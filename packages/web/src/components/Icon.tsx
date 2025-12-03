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
import ResolvePhase from "@mui/icons-material/CheckBoxOutlined";
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
import Sandbox from "@mui/icons-material/Widgets";
import Edit from "@mui/icons-material/Edit";
import PersonAdd from "@mui/icons-material/PersonAdd";
import PersonRemove from "@mui/icons-material/PersonRemove";
import Trophy from "@mui/icons-material/EmojiEvents";
import { SxProps, Theme } from "@mui/material";

import {
  Home as LucideHome,
  Search as LucideSearch,
  PlusCircle as LucidePlusCircle,
  User as LucideUser,
  ArrowLeft as LucideArrowLeft,
  SearchX as LucideSearchX,
  Inbox as LucideInbox,
  Calendar as LucideCalendar,
  Flag as LucideFlag,
  Users as LucideUsers,
  MoreHorizontal as LucideMoreHorizontal,
  MessageCircle as LucideMessageCircle,
  Gavel as LucideGavel,
  CheckSquare as LucideCheckSquare,
  Square as LucideSquare,
  Check as LucideCheck,
  Map as LucideMap,
  UserPlus as LucideUserPlus,
  MessageSquare as LucideMessageSquare,
  XCircle as LucideXCircle,
  X as LucideX,
  Trash2 as LucideTrash2,
  Maximize as LucideMaximize,
  Minimize as LucideMinimize,
  Lock as LucideLock,
  Clock as LucideClock,
  Star as LucideStar,
  Edit as LucideEdit,
  UserMinus as LucideUserMinus,
  Trophy as LucideTrophy,
  type LucideIcon,
  LucideBlocks,
} from "lucide-react";

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
  Sandbox = "sandbox",
  ResolvePhase = "resolve-phase",
  Edit = "edit",
  Join = "join",
  Leave = "leave",
  Trophy = "trophy",
}

const MuiIconMap = {
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
  [IconName.Sandbox]: Sandbox,
  [IconName.ResolvePhase]: ResolvePhase,
  [IconName.Edit]: Edit,
  [IconName.Join]: PersonAdd,
  [IconName.Leave]: PersonRemove,
  [IconName.Trophy]: Trophy,
};

const LucideIconMap: Record<IconName, LucideIcon> = {
  [IconName.MyGames]: LucideHome,
  [IconName.FindGames]: LucideSearch,
  [IconName.CreateGame]: LucidePlusCircle,
  [IconName.Add]: LucidePlusCircle,
  [IconName.Profile]: LucideUser,
  [IconName.Back]: LucideArrowLeft,
  [IconName.NoResults]: LucideSearchX,
  [IconName.Empty]: LucideInbox,
  [IconName.StartYear]: LucideCalendar,
  [IconName.WinCondition]: LucideFlag,
  [IconName.Players]: LucideUsers,
  [IconName.Failure]: LucideX,
  [IconName.Author]: LucideUser,
  [IconName.Menu]: LucideMoreHorizontal,
  [IconName.Chat]: LucideMessageCircle,
  [IconName.Orders]: LucideGavel,
  [IconName.CreateOrder]: LucidePlusCircle,
  [IconName.OrdersConfirmed]: LucideCheckSquare,
  [IconName.OrdersNotConfirmed]: LucideSquare,
  [IconName.Success]: LucideCheck,
  [IconName.Map]: LucideMap,
  [IconName.GroupAdd]: LucideUserPlus,
  [IconName.NoChannels]: LucideMessageSquare,
  [IconName.Cancel]: LucideXCircle,
  [IconName.Close]: LucideX,
  [IconName.Delete]: LucideTrash2,
  [IconName.Fullscreen]: LucideMaximize,
  [IconName.FullscreenExit]: LucideMinimize,
  [IconName.Lock]: LucideLock,
  [IconName.Clock]: LucideClock,
  [IconName.Star]: LucideStar,
  [IconName.Sandbox]: LucideBlocks,
  [IconName.ResolvePhase]: LucideCheckSquare,
  [IconName.Edit]: LucideEdit,
  [IconName.Join]: LucideUserPlus,
  [IconName.Leave]: LucideUserMinus,
  [IconName.Trophy]: LucideTrophy,
};

interface IconProps {
  name: IconName;
  sx?: SxProps<Theme>;
  variant?: "mui" | "lucide";
  className?: string;
  size?: number;
  highlight?: boolean;
}

const Icon: React.FC<IconProps> = ({
  name,
  variant = "mui",
  sx,
  className,
  size,
  highlight = false,
  ...rest
}) => {
  if (variant === "lucide") {
    const LucideIconComponent = LucideIconMap[name];
    const strokeWidth = highlight ? 2.5 : 1.5;
    return (
      <LucideIconComponent
        className={className}
        size={size}
        strokeWidth={strokeWidth}
        {...rest}
      />
    );
  }

  const MuiIconComponent = MuiIconMap[name];
  return <MuiIconComponent sx={sx} {...rest} />;
};

export { Icon, IconName };
