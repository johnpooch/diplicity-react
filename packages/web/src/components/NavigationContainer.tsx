import React from "react";
import { useNavigate, useLocation } from "react-router";
import { Navigation } from "./Navigation";
import { navigationItems } from "../navigation/navigationItems";

interface NavigationContainerProps {
  variant: "sidebar" | "compact" | "bottom";
  className?: string;
}

const NavigationContainer: React.FC<NavigationContainerProps> = ({
  variant,
  className,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleItemClick = (path: string) => {
    navigate(path);
  };

  const itemsWithActiveState = navigationItems.map((item) => ({
    ...item,
    isActive: location.pathname === item.path,
  }));

  return (
    <Navigation
      items={itemsWithActiveState}
      variant={variant}
      onItemClick={handleItemClick}
      className={className}
    />
  );
};

export { NavigationContainer };
export type { NavigationContainerProps };
