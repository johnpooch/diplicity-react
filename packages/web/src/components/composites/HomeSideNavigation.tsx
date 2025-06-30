import { useNavigate } from "react-router";
import { IconName } from "../elements/Icon";
import { useResponsiveness } from "../utils/responsive";
import { useEffect, useState } from "react";
import { SideNavigation } from "../elements/SideNavigation";

const NavigationItems = [
    { label: "My Games", icon: IconName.MyGames, value: "/" },
    { label: "Find Games", icon: IconName.FindGames, value: "/find-games" },
    { label: "Create Game", icon: IconName.CreateGame, value: "/create-game" },
    { label: "Profile", icon: IconName.Profile, value: "/profile" },
];

const HomeSideNavigation: React.FC = () => {
    const navigate = useNavigate();
    const responsiveness = useResponsiveness();
    const [navigation, setNavigation] = useState(location.pathname);

    useEffect(() => {
        setNavigation(location.pathname);
    }, [location.pathname]);

    const handleNavigationChange = (newValue: string) => {
        setNavigation(newValue);
        navigate(newValue);
    };

    return (
        <SideNavigation
            options={NavigationItems}
            selectedValue={navigation}
            onChange={handleNavigationChange}
            variant={responsiveness.device === "desktop" ? "expanded" : "collapsed"}
        />
    );
};

export { HomeSideNavigation };
