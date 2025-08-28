import { useNavigate } from "react-router";
import { IconName } from "../../Icon";
import { useResponsiveness } from "../../utils/responsive";
import { SideNavigation } from "../../SideNavigation";

const HomeSideNavigation: React.FC = () => {
  const navigate = useNavigate();
  const responsiveness = useResponsiveness();

  const navigationItems = [
    {
      label: "My Games",
      icon: IconName.MyGames,
      path: "/",
      onClick: () => navigate("/"),
    },
    {
      label: "Find Games",
      icon: IconName.FindGames,
      path: "/find-games",
      onClick: () => navigate("/find-games"),
    },
    {
      label: "Create Game",
      icon: IconName.CreateGame,
      path: "/create-game",
      onClick: () => navigate("/create-game"),
    },
    {
      label: "Profile",
      icon: IconName.Profile,
      path: "/profile",
      onClick: () => navigate("/profile"),
    },
  ];

  return (
    <SideNavigation
      options={navigationItems}
      variant={responsiveness.device === "desktop" ? "expanded" : "collapsed"}
    />
  );
};

export { HomeSideNavigation };
