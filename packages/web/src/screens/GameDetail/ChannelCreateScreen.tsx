import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AxiosError } from "axios";
import { toast } from "sonner";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { NationFlag, findNationFlagUrl, findNationColor } from "@/components/NationFlag";
import { cn } from "@/lib/utils";
import { useGameVariant } from "@/hooks/useGameVariant";
import { GameDetailAppBar } from "./AppBar";
import { Panel } from "../../components/Panel";
import {
  getGamesChannelsListQueryKey,
  useGameRetrieveSuspense,
  useGamesChannelsCreateCreate,
  type Channel,
  type Member,
} from "@/api/generated/endpoints";

const channelSchema = z.object({
  memberIds: z.array(z.number()).min(1),
});

type ChannelFormValues = z.infer<typeof channelSchema>;

const createChannelErrorMessage = (error: unknown, fallback: string) => {
  const data = (error as AxiosError<{ memberIds?: string[]; detail?: string }>)
    .response?.data;
  return data?.memberIds?.[0] ?? data?.detail ?? fallback;
};

const roleLabel = (member: Member): string | undefined => {
  if (member.isBot) return "bot";
  return undefined;
};

const MemberRow: React.FC<{
  member: Member;
  nationFlagUrl: string | null;
  nationColor: string | null;
  selected: boolean;
  disabled: boolean;
  onToggle: () => void;
}> = ({ member, nationFlagUrl, nationColor, selected, disabled, onToggle }) => {
  const role = roleLabel(member);
  const nation = member.nation ?? member.name;

  return (
    <label
      className={cn(
        "flex w-full cursor-pointer items-center gap-3 p-3 transition-colors hover:bg-accent/50",
        selected && "bg-accent/50"
      )}
    >
      <div className="relative size-12 shrink-0">
        <NationFlag
          flagUrl={nationFlagUrl}
          alt={nation}
          size="lg"
          className="size-12"
          color={nationColor}
        />
        <span className="absolute -bottom-0.5 -right-0.5">
          <Avatar className="size-5 ring-2 ring-card">
            <AvatarImage src={member.picture ?? undefined} />
            <AvatarFallback className="text-[8px]">
              {member.name[0]?.toUpperCase() ?? "?"}
            </AvatarFallback>
          </Avatar>
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold leading-tight">{nation}</p>
        <p className="truncate text-sm text-muted-foreground">
          {member.name}
          {role && ` (${role})`}
        </p>
      </div>
      <Checkbox
        checked={selected}
        onCheckedChange={onToggle}
        disabled={disabled}
        aria-label={`Select ${nation}`}
      />
    </label>
  );
};

const ChannelCreateScreen: React.FC = () => {
  const { gameId, phaseId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
  }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: game } = useGameRetrieveSuspense(gameId);
  const variant = useGameVariant(game);
  const variantNations = variant?.nations ?? [];
  const createChannelMutation = useGamesChannelsCreateCreate();

  const form = useForm<ChannelFormValues>({
    resolver: zodResolver(channelSchema),
    defaultValues: { memberIds: [] },
  });

  const handleCreateChannel = async (values: ChannelFormValues) => {
    try {
      const response = await createChannelMutation.mutateAsync({
        gameId: gameId,
        data: {
          memberIds: values.memberIds,
        },
      });
      queryClient.setQueryData<Channel[]>(
        getGamesChannelsListQueryKey(gameId),
        (old) => [...(old ?? []), response]
      );
      toast.success("Channel created successfully");
      if (response) {
        navigate(`/game/${gameId}/phase/${phaseId}/chat/channel/${response.id}`);
      }
    } catch (error) {
      toast.error(createChannelErrorMessage(error, "Failed to create channel"));
    }
  };

  const handleBack = () => {
    navigate(`/game/${gameId}/phase/${phaseId}/chat`);
  };

  const isSubmitting = createChannelMutation.isPending;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Create channel"
        variant="secondary"
        onNavigateBack={handleBack}
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(handleCreateChannel)}
                className="flex flex-col gap-4 px-3 py-4"
              >
                <FormField
                  control={form.control}
                  name="memberIds"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-muted-foreground">Members</FormLabel>
                      <FormControl>
                        <Card className="overflow-hidden py-0">
                          <CardContent className="flex flex-col divide-y p-0">
                            {game.members
                              .filter(m => !m.isCurrentUser && !m.kicked)
                              .map(member => (
                                <MemberRow
                                  key={member.id}
                                  member={member}
                                  nationFlagUrl={findNationFlagUrl(variantNations, member.nation)}
                                  nationColor={findNationColor(variantNations, member.nation)}
                                  selected={field.value.includes(member.id)}
                                  disabled={isSubmitting}
                                  onToggle={() =>
                                    field.onChange(
                                      field.value.includes(member.id)
                                        ? field.value.filter(id => id !== member.id)
                                        : [...field.value, member.id]
                                    )
                                  }
                                />
                              ))}
                          </CardContent>
                        </Card>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={form.watch("memberIds").length === 0 || isSubmitting}
                >
                  Create channel
                </Button>
              </form>
            </Form>
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

const ChannelCreateScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div></div>}>
      <ChannelCreateScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { ChannelCreateScreenSuspense as ChannelCreateScreen };
