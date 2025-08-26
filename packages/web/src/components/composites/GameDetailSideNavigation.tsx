import { useNavigate, useParams } from "react-router";
import { IconName } from "../elements/Icon";
import { SideNavigation } from "../elements/SideNavigation";

const GameDetailSideNavigation: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("Game ID is required");

  const navigate = useNavigate();
  const navigationItems = [
    {
      label: "Back",
      icon: IconName.Back,
      path: "/",
      onClick: () => navigate("/"),
    },
    {
      label: "Orders",
      icon: IconName.Orders,
      path: "/game/:gameId",
      onClick: () => navigate(`/game/${gameId}`),
    },
    {
      label: "Chat",
      icon: IconName.Chat,
      path: "/game/:gameId/chat",
      onClick: () => navigate(`/game/${gameId}/chat`),
    },
  ];

  return <SideNavigation options={navigationItems} variant="collapsed" />;
};

export { GameDetailSideNavigation };
