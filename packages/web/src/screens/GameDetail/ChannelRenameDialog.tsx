import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Pencil } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  getGamesChannelsListQueryKey,
  useGamesChannelsPartialUpdate,
  type Channel,
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

interface ChannelRenameDialogProps {
  gameId: string;
  channel: Channel;
}

const ChannelRenameDialog: React.FC<ChannelRenameDialogProps> = ({
  gameId,
  channel,
}) => {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const renameMutation = useGamesChannelsPartialUpdate();

  const form = useForm<RenameFormValues>({
    resolver: zodResolver(renameSchema),
    defaultValues: { title: channel.title ?? "" },
  });

  const handleOpenChange = (open: boolean) => {
    if (open) form.reset({ title: channel.title ?? "" });
    setIsOpen(open);
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
      setIsOpen(false);
    } catch {
      toast.error("Failed to rename channel");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="icon-sm"
          className="rounded-full"
          aria-label="Rename channel"
        >
          <Pencil />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Rename channel</DialogTitle>
          <DialogDescription>
            Everyone in this channel sees the new name, and that it was you who
            changed it.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleRename)}
            className="flex flex-col gap-4"
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
            <DialogFooter>
              <Button type="submit" disabled={renameMutation.isPending}>
                Save
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export { ChannelRenameDialog };
