import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "@/components/Panel";
import {
  getGamesChannelsListQueryKey,
  useGamesChannelsListSuspense,
  useGamesChannelsPartialUpdate,
} from "@/api/generated/endpoints";

const CHANNEL_TITLE_MAX_LENGTH = 50;

const renameSchema = z.object({
  title: z
    .string()
    .min(1, "Channel name is required")
    .max(
      CHANNEL_TITLE_MAX_LENGTH,
      `Channel names cannot be longer than ${CHANNEL_TITLE_MAX_LENGTH} characters.`
    ),
});

type RenameFormValues = z.infer<typeof renameSchema>;

const ChannelRenameScreen: React.FC = () => {
  const { gameId, phaseId, channelId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    channelId: string;
  }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: channels } = useGamesChannelsListSuspense(gameId);
  const channel = channels.find(c => c.id === parseInt(channelId));
  if (!channel) throw new Error("Channel not found");

  const renameMutation = useGamesChannelsPartialUpdate();

  const form = useForm<RenameFormValues>({
    resolver: zodResolver(renameSchema),
    defaultValues: { title: channel.title ?? "" },
  });

  const handleBack = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/chat/channel/${channelId}`);
  };

  const handleRename = async (values: RenameFormValues) => {
    try {
      await renameMutation.mutateAsync({
        gameId,
        channelId: channel.id,
        data: { title: values.title },
      });
      queryClient.invalidateQueries({
        queryKey: getGamesChannelsListQueryKey(gameId),
      });
      handleBack();
    } catch {
      toast.error("Failed to rename channel");
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Rename channel"
        variant="secondary"
        onNavigateBack={handleBack}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(handleRename)}
                className="flex flex-col gap-4 px-3 py-4"
              >
                <FormField
                  control={form.control}
                  name="title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Channel name</FormLabel>
                      <FormControl>
                        <Input
                          maxLength={CHANNEL_TITLE_MAX_LENGTH}
                          disabled={renameMutation.isPending}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={renameMutation.isPending}
                >
                  Rename channel
                </Button>
              </form>
            </Form>
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const ChannelRenameScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <ChannelRenameScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { ChannelRenameScreenSuspense as ChannelRenameScreen };
