import React from "react";
import { useNavigate } from "react-router";
import { MoreHorizontal } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuAction,
} from "@/components/ui/sidebar";
import { useUserRetrieveSuspense } from "@/api/generated/endpoints";
import { useAuth } from "@/auth";

const SidebarUserArea: React.FC = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { data: userProfile } = useUserRetrieveSuspense();

  const handleClick = () => {
    navigate("/profile");
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton size="lg" onClick={handleClick} tooltip="Profile">
          <Avatar className="size-8">
            <AvatarImage src={userProfile?.picture ?? undefined} />
            <AvatarFallback>
              {userProfile?.name?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <span className="truncate">{userProfile?.name}</span>
        </SidebarMenuButton>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuAction aria-label="Menu">
              <MoreHorizontal />
            </SidebarMenuAction>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="end">
            <DropdownMenuItem onClick={handleLogout}>Logout</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
};

export { SidebarUserArea };
