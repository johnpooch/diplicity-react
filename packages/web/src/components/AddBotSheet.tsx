import React, { Suspense } from "react";
import { Bot } from "lucide-react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { Notice } from "@/components/Notice";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  AvailableBot,
  getGameAvailableBotsListQueryKey,
  getGameRetrieveQueryKey,
  useGameAddBotCreate,
  useGameAvailableBotsListSuspense,
} from "@/api/generated/endpoints";
import { useIsMobile } from "@/hooks/use-mobile";

interface AvailableBotListProps {
  gameId: string;
}

const AvailableBotList: React.FC<AvailableBotListProps> = ({ gameId }) => {
  const { data: bots } = useGameAvailableBotsListSuspense(gameId);
  const queryClient = useQueryClient();
  const addBotMutation = useGameAddBotCreate();

  const handleAdd = async (bot: AvailableBot) => {
    try {
      await addBotMutation.mutateAsync({
        gameId,
        data: { userId: bot.userId },
      });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: getGameRetrieveQueryKey(gameId),
        }),
        queryClient.invalidateQueries({
          queryKey: getGameAvailableBotsListQueryKey(gameId),
        }),
      ]);
      toast.success(`${bot.name} joined the game`);
    } catch {
      toast.error("Failed to add AI player");
    }
  };

  if (bots.length === 0) {
    return (
      <Notice
        title="No AI players available"
        message="Every AI player is already in this game."
        icon={Bot}
      />
    );
  }

  return (
    <div className="flex flex-col divide-y">
      {bots.map(bot => (
        <button
          key={bot.userId}
          onClick={() => handleAdd(bot)}
          disabled={addBotMutation.isPending}
          className="flex items-center gap-4 py-3 px-2 text-left hover:bg-accent disabled:opacity-50"
        >
          <Avatar className="size-8">
            <AvatarImage src={bot.picture ?? undefined} />
            <AvatarFallback>
              <Bot className="size-4" />
            </AvatarFallback>
          </Avatar>
          <span className="font-medium">{bot.name}</span>
        </button>
      ))}
    </div>
  );
};

const AvailableBotListSkeleton: React.FC = () => (
  <div className="flex flex-col divide-y">
    {Array.from({ length: 6 }, (_, index) => (
      <div key={index} className="flex items-center gap-4 py-3 px-2">
        <Skeleton className="size-8 rounded-full" />
        <Skeleton className="h-4 w-32" />
      </div>
    ))}
  </div>
);

interface AddBotSheetProps {
  gameId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const AddBotSheet: React.FC<AddBotSheetProps> = ({
  gameId,
  open,
  onOpenChange,
}) => {
  const isMobile = useIsMobile();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side={isMobile ? "bottom" : "right"}
        className={isMobile ? "rounded-t-lg max-h-[80vh]" : undefined}
      >
        <SheetHeader>
          <SheetTitle>Add AI player</SheetTitle>
          <SheetDescription>
            Choose an AI player to fill an open seat. It plays and chats like
            any other player.
          </SheetDescription>
        </SheetHeader>
        <div className="overflow-y-auto px-4 pb-4">
          <QueryErrorBoundary>
            <Suspense fallback={<AvailableBotListSkeleton />}>
              <AvailableBotList gameId={gameId} />
            </Suspense>
          </QueryErrorBoundary>
        </div>
      </SheetContent>
    </Sheet>
  );
};
