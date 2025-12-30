import React from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  MoreHorizontal,
  UserPlus,
  Info,
  Users,
  Share,
} from "lucide-react";
import { Skeleton } from "./ui/skeleton";

export interface GameCardSkeletonProps {
  className?: string;
}

const GameCardSkeleton: React.FC<GameCardSkeletonProps> = () => {
  return (
    <Card className="w-full flex flex-col md:flex-row overflow-hidden p-0">
      {/* 1. Map (SVG) Section - Top on mobile, Left on larger screens */}
      <div className="md:max-w-xs lg:max-w-sm">
        <Skeleton className="w-full h-64 md:h-full" />
      </div>

      {/* 2. Content Container - Right Side */}
      <div className="flex flex-col justify-between flex-grow p-4">
        {/* Header (Title, Subtitle, and More Button) */}
        <CardHeader className="p-0">
          <div className="flex flex-col">
            {/* Title and Menu Group */}
            <div className="flex justify-between items-center">
              <CardTitle>
                <Skeleton className="w-48 h-6" />
              </CardTitle>
              {/* More Actions Button */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>
                    <Info />
                    Game info
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Users />
                    Player info
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <Share />
                    Share
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <CardDescription className="text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Skeleton className="w-32 h-4" />
              </div>
              <Skeleton className="w-40 h-4 mt-1" />
            </CardDescription>
          </div>
        </CardHeader>
        <CardFooter className="p-0 flex justify-between items-center">
          <div className="flex -space-x-2">
            <Skeleton className="w-8 h-8 rounded-full" />
            <Skeleton className="w-8 h-8 rounded-full" />
            <Skeleton className="w-8 h-8 rounded-full" />
          </div>

          <Button variant="outline" disabled>
            <UserPlus />
            Join
          </Button>
        </CardFooter>
      </div>
    </Card>
  );
};

export { GameCardSkeleton };
