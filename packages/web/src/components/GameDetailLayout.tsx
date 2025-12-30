import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { cn } from "@/lib/utils";
import { Navigation } from "@/components/Navigation";
import { gameDetailNavigationItems } from "@/navigation/navigationItems";
import {
  ArrowLeft,
  PanelLeftClose,
  PanelLeftOpen,
  Check,
  Plus,
} from "lucide-react";
import { Button } from "./ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "./ui/separator";
import { Tabs, TabsTrigger, TabsList, TabsContent } from "./ui/tabs";
import { ScrollArea } from "./ui/scroll-area";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Flags } from "@/assets/flags";
import {
  Item,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemSeparator,
  ItemTitle,
} from "@/components/ui/item";

interface GameDetailLayoutProps {
  className?: string;
  isPanelOpen?: boolean;
  onPanelToggle?: () => void;
}

const GameDetailLayout: React.FC<GameDetailLayoutProps> = ({
  className,
  isPanelOpen = false,
  onPanelToggle,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const gameId = React.useMemo(() => {
    const match = location.pathname.match(/^\/game\/([^/]+)/);
    return match?.[1];
  }, [location.pathname]);

  const [selectedStatus, setSelectedStatus] = useState<string>("orders");

  const navItems = React.useMemo(() => {
    const resolvePath = (pathTemplate: string) =>
      gameId ? pathTemplate.replace(":gameId", gameId) : pathTemplate;

    return gameDetailNavigationItems.map(item => {
      const path = resolvePath(item.path);
      return {
        ...item,
        path,
        isActive: location.pathname === path,
      };
    });
  }, [gameId, location.pathname]);

  const currentNavPath = navItems.find(item => item.isActive)?.path;

  const bottomClasses = cn("border-t bg-background", "block md:hidden");

  return (
    <div
      className={cn("flex flex-col h-screen w-full overflow-hidden", className)}
    >
      <div className="flex items-stretch flex-1 min-h-0 w-full">
        {/* Full screen map */}
        <div className="flex-1">
          <svg viewBox="0 0 1200 600">
            <defs>
              <pattern
                id="horizontalStripes"
                width="20"
                height="20"
                patternUnits="userSpaceOnUse"
              >
                <rect width="20" height="10" fill="#e2e8f0" />
                <rect y="10" width="20" height="10" fill="#cbd5e1" />
              </pattern>
            </defs>
            <rect width="800" height="600" fill="url(#horizontalStripes)" />
            <text
              x="400"
              y="300"
              fontSize="48"
              fill="#64748b"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              Map
            </text>
          </svg>
        </div>
        {/* Floating menu with border and radius */}
        <div className="absolute top-4 left-4 w-[370px] max-h-[80vh] border border-gray-200 rounded-lg bg-background flex flex-col shadow-sm overflow-hidden">
          <div className="flex items-center gap-1 w-full p-1 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Back"
              onClick={() => navigate(-1)}
            >
              <ArrowLeft />
            </Button>

            {/* No border on the select */}
            <Select
              value={currentNavPath}
              onValueChange={path => navigate(path)}
            >
              <SelectTrigger
                size="sm"
                className="flex-1 border-none shadow-none"
              >
                <SelectValue placeholder="Navigate" />
              </SelectTrigger>
              <SelectContent>
                {navItems.map(item => (
                  <SelectItem key={item.path} value={item.path}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Expand menu button */}
            <Button
              variant="ghost"
              size="icon"
              aria-label="Expand menu"
              onClick={onPanelToggle}
            >
              {isPanelOpen ? <PanelLeftClose /> : <PanelLeftOpen />}
            </Button>
          </div>

          {/* Collapsible panel under the floating menu */}
          {isPanelOpen && (
            <>
              <Separator className="shrink-0" />
              <div className="w-full flex-1 flex flex-col min-h-0 p-1 py-2">
                <Tabs
                  value={selectedStatus}
                  onValueChange={value => setSelectedStatus(value)}
                  className="w-full flex flex-col flex-1 min-h-0 gap-0"
                >
                  <TabsList className="w-full shrink-0 mb-2">
                    <TabsTrigger value="orders" className="flex-1">
                      Orders
                    </TabsTrigger>
                    <TabsTrigger value="chat" className="flex-1">
                      Chat
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent
                    value="orders"
                    className="flex-1 flex flex-col mt-0 overflow-hidden"
                  >
                    <ScrollArea className="flex-1 min-h-0 -mr-1 overflow-scroll">
                      <div className="pr-4">
                        <Accordion
                          type="single"
                          collapsible
                          className="w-full"
                          defaultValue="england"
                        >
                          <AccordionItem value="england">
                            <AccordionTrigger className="py-3">
                              <div className="flex items-center gap-2">
                                <img
                                  src={Flags.classical.england}
                                  alt="England"
                                  className="size-5 shrink-0 rounded-full"
                                />
                                <span>England</span>
                              </div>
                            </AccordionTrigger>
                            <AccordionContent className="pb-2">
                              <ItemGroup className="gap-1">
                                <Item size="sm">
                                  <ItemContent>
                                    <ItemTitle>Fleet Baltic Sea</ItemTitle>
                                    <ItemDescription>
                                      No order provided
                                    </ItemDescription>
                                  </ItemContent>
                                </Item>
                                <ItemSeparator />
                                <Item size="sm">
                                  <ItemContent>
                                    <ItemTitle>Fleet Denmark</ItemTitle>
                                    <ItemDescription>
                                      No order provided
                                    </ItemDescription>
                                  </ItemContent>
                                </Item>
                                <ItemSeparator />
                                <Item size="sm">
                                  <ItemContent>
                                    <ItemTitle>Fleet Denmark</ItemTitle>
                                    <ItemDescription>
                                      No order provided
                                    </ItemDescription>
                                  </ItemContent>
                                </Item>
                                <ItemSeparator />
                                <Item size="sm">
                                  <ItemContent>
                                    <ItemTitle>Fleet Denmark</ItemTitle>
                                    <ItemDescription>
                                      No order provided
                                    </ItemDescription>
                                  </ItemContent>
                                </Item>
                                <ItemSeparator />
                                <Item size="sm">
                                  <ItemContent>
                                    <ItemTitle>Fleet Denmark</ItemTitle>
                                    <ItemDescription>
                                      No order provided
                                    </ItemDescription>
                                  </ItemContent>
                                </Item>
                                <ItemSeparator />
                                <Item size="sm">
                                  <ItemContent>
                                    <ItemTitle>Fleet Denmark</ItemTitle>
                                    <ItemDescription>
                                      No order provided
                                    </ItemDescription>
                                  </ItemContent>
                                </Item>
                                <ItemSeparator />
                                <Item size="sm">
                                  <ItemContent>
                                    <ItemTitle>Fleet Denmark</ItemTitle>
                                    <ItemDescription>
                                      No order provided
                                    </ItemDescription>
                                  </ItemContent>
                                </Item>
                              </ItemGroup>
                            </AccordionContent>
                          </AccordionItem>
                        </Accordion>
                      </div>
                    </ScrollArea>
                    <div className="pt-2 shrink-0">
                      <Button className="w-full" size="sm">
                        <Check />
                        Confirm Orders
                      </Button>
                    </div>
                  </TabsContent>
                  <TabsContent
                    value="chat"
                    className="flex-1 flex flex-col mt-0 overflow-hidden"
                  >
                    <ScrollArea className="flex-1 min-h-0 -mr-1 overflow-scroll">
                      <div className="pr-4">
                        <ItemGroup className="gap-1">
                          <Item size="sm">
                            <ItemContent>
                              <ItemTitle>Public Press</ItemTitle>
                              <ItemDescription>
                                Russia: not on my mobile
                              </ItemDescription>
                            </ItemContent>
                          </Item>
                          <ItemSeparator />
                          <Item size="sm">
                            <ItemContent>
                              <ItemTitle>Russia, Turkey</ItemTitle>
                              <ItemDescription>
                                England: I like it
                              </ItemDescription>
                            </ItemContent>
                          </Item>
                        </ItemGroup>
                      </div>
                    </ScrollArea>
                    <div className="pt-2 shrink-0">
                      <Button className="w-full" size="sm">
                        <Plus />
                        Create Channel
                      </Button>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className={bottomClasses}>
        <Navigation
          items={navItems}
          variant="bottom"
          onItemClick={path => navigate(path)}
        />
      </div>
    </div>
  );
};

export { GameDetailLayout };
export type { GameDetailLayoutProps };
