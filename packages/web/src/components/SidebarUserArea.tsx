import React from "react";
import { useNavigate } from "react-router";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar";
import { useUserRetrieveSuspense } from "@/api/generated/endpoints";

const SidebarUserArea: React.FC = () => {
  const navigate = useNavigate();
  const { data: userProfile } = useUserRetrieveSuspense();

  const handleClick = () => {
    navigate("/profile");
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          size="lg"
          onClick={handleClick}
          tooltip="Profile"
        >
          <Avatar className="size-8">
            <AvatarImage src={userProfile?.picture ?? undefined} />
            <AvatarFallback>
              {userProfile?.name?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <span className="truncate">{userProfile?.name}</span>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
};

export { SidebarUserArea };
