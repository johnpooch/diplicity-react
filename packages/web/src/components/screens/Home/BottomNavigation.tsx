import { useNavigate } from "react-router";
import { IconName } from "../../Icon";
import { useEffect, useState } from "react";
import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  Stack,
} from "@mui/material";
import { Icon } from "../../Icon";

const NavigationItems = [
  { label: "My Games", icon: IconName.MyGames, value: "/" },
  { label: "Find Games", icon: IconName.FindGames, value: "/find-games" },
  { label: "Create Game", icon: IconName.CreateGame, value: "/create-game" },
  { label: "Profile", icon: IconName.Profile, value: "/profile" },
];

const HomeBottomNavigation: React.FC = () => {
  const navigate = useNavigate();
  const [navigation, setNavigation] = useState(location.pathname);

  useEffect(() => {
    setNavigation(location.pathname);
  }, [location.pathname]);

  const handleNavigationChange = (
    _event: React.SyntheticEvent,
    newValue: string
  ) => {
    setNavigation(newValue);
    navigate(newValue);
  };

  return (
    <>
      <Stack sx={{ height: 56 }} />
      <AppBar position="fixed" color="primary" sx={{ top: "auto", bottom: 0 }}>
        <BottomNavigation value={navigation} onChange={handleNavigationChange}>
          {NavigationItems.map(item => (
            <BottomNavigationAction
              key={item.value}
              icon={<Icon name={item.icon} />}
              value={item.value}
            />
          ))}
        </BottomNavigation>
      </AppBar>
    </>
  );
};

export { HomeBottomNavigation };
