import { useNavigate, useParams } from "react-router";
import { IconName } from "../../components/Icon";
import { useEffect, useState } from "react";
import {
    AppBar,
    BottomNavigation,
    BottomNavigationAction,
} from "@mui/material";
import { Icon } from "../../components/Icon";

const GameDetailBottomNavigation: React.FC = () => {
    const navigate = useNavigate();
    const { gameId } = useParams<{ gameId: string }>();
    const [navigation, setNavigation] = useState(location.pathname);

    if (!gameId) throw new Error("Game ID is required");

    const NavigationItems = [
        { label: "Map", icon: IconName.Map, value: `/game/${gameId}` },
        { label: "Orders", icon: IconName.Orders, value: `/game/${gameId}/orders` },
        { label: "Chat", icon: IconName.Chat, value: `/game/${gameId}/chat` },
    ];

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
    );
};

export { GameDetailBottomNavigation };
