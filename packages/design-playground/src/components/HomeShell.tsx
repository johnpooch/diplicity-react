import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { Item, ItemContent, ItemMedia, ItemTitle } from "@/components/ui/item";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { DiplicityLogo } from "@/components/DiplicityLogo";
import { Navigation } from "@/components/Navigation";
import { cn } from "@/lib/utils";
import {
  CircleHelp,
  Home,
  MessageCircle,
  PlusCircle,
  Search,
} from "lucide-react";

const navigationItems = [
  { label: "My Games", icon: Home },
  { label: "Find Games", icon: Search },
  { label: "Create Game", icon: PlusCircle },
  { label: "Community", icon: MessageCircle },
];

interface HomeShellProps {
  children: React.ReactNode;
  activeNavItem?: string;
  className?: string;
}

const HomeShell: React.FC<HomeShellProps> = ({
  children,
  activeNavItem = "My Games",
  className,
}) => {
  const items = navigationItems.map(item => ({
    ...item,
    isActive: item.label === activeNavItem,
  }));

  return (
    <SidebarProvider>
      <div
        className={cn(
          "flex h-dvh w-full flex-col overflow-hidden",
          className
        )}
      >
        <div className="flex min-h-0 w-full flex-1 items-stretch">
          <Sidebar collapsible="icon">
            <SidebarHeader>
              <Item className="p-1">
                <ItemMedia variant="image">
                  <DiplicityLogo />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>Diplicity</ItemTitle>
                </ItemContent>
              </Item>
            </SidebarHeader>
            <SidebarContent>
              <Navigation items={items} variant="sidebar" />
            </SidebarContent>
            <SidebarFooter>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton tooltip="Learn how to play">
                    <CircleHelp />
                    <span>Learn how to play</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton tooltip="otto">
                    <Avatar className="size-5">
                      <AvatarFallback className="text-[10px]">O</AvatarFallback>
                    </Avatar>
                    <span>otto</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarFooter>
          </Sidebar>

          <SidebarInset className="flex min-w-0 flex-1 flex-col">
            <div className="@container flex-1 overflow-y-auto">
              <div className="mx-auto w-full max-w-[672px] px-2 py-4">
                {children}
              </div>
            </div>
          </SidebarInset>
        </div>

        <div className="block border-t bg-background md:hidden">
          <Navigation items={items} variant="bottom" />
        </div>
      </div>
    </SidebarProvider>
  );
};

export { HomeShell };
