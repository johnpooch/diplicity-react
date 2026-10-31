import React, { Suspense } from "react";
import { Link, useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useRequiredParams } from "@/hooks";

import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
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
  getGameMemberRetrieveQueryKey,
  useGameMemberReportCreate,
  useReportReasonsListSuspense,
  ReasonEnum,
} from "@/api/generated/endpoints";

const NOTE_MAX_LENGTH = 1000;

const reportSchema = z.object({
  reason: z.nativeEnum(ReasonEnum, { message: "Pick a reason" }),
  note: z
    .string()
    .trim()
    .min(1, "Add a note describing what happened")
    .max(NOTE_MAX_LENGTH, `Notes cannot be longer than ${NOTE_MAX_LENGTH} characters.`),
});

type ReportFormValues = z.infer<typeof reportSchema>;

const ReportMemberForm: React.FC = () => {
  const { gameId, phaseId, memberId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    memberId: string;
  }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: reasons } = useReportReasonsListSuspense();
  const reportMutation = useGameMemberReportCreate();

  const form = useForm<ReportFormValues>({
    resolver: zodResolver(reportSchema),
    defaultValues: { reason: undefined, note: "" },
  });

  const handleReport = async (values: ReportFormValues) => {
    try {
      await reportMutation.mutateAsync({
        gameId,
        memberId: Number(memberId),
        data: values,
      });
      await queryClient.invalidateQueries({
        queryKey: getGameMemberRetrieveQueryKey(gameId, Number(memberId)),
      });
      toast.success("Report submitted");
      navigate(`/game/${gameId}/phase/${phaseId}/member/${memberId}`);
    } catch {
      toast.error("Failed to submit report");
    }
  };

  const isSubmitting = reportMutation.isPending;

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(handleReport)}
        className="flex flex-col gap-4"
      >
        <FormField
          control={form.control}
          name="reason"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Reason</FormLabel>
              <FormControl>
                <Card className="overflow-hidden py-0">
                  <CardContent className="p-0">
                    <RadioGroup
                      value={field.value ?? ""}
                      onValueChange={field.onChange}
                      disabled={isSubmitting}
                      className="gap-0 divide-y"
                    >
                      {reasons.map(reason => (
                        <label
                          key={reason.key}
                          className="flex cursor-pointer items-start gap-3 p-3 hover:bg-accent/50"
                        >
                          <RadioGroupItem value={reason.key} className="mt-0.5" />
                          <span className="flex flex-col gap-1">
                            <span className="text-sm font-medium">{reason.label}</span>
                            <span className="text-sm text-muted-foreground">
                              {reason.description}
                            </span>
                          </span>
                        </label>
                      ))}
                    </RadioGroup>
                  </CardContent>
                </Card>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="note"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Note</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="What happened?"
                  maxLength={NOTE_MAX_LENGTH}
                  disabled={isSubmitting}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          Submit report
        </Button>
      </form>
    </Form>
  );
};

const ReportMemberFormSkeleton: React.FC = () => (
  <div className="flex flex-col gap-4">
    <Skeleton className="h-4 w-16" />
    <Skeleton className="h-[300px] w-full rounded-xl" />
    <Skeleton className="h-4 w-12" />
    <Skeleton className="h-16 w-full" />
    <Skeleton className="h-10 w-full" />
  </div>
);

const ReportMemberScreen: React.FC = () => {
  const navigate = useNavigate();
  const { gameId, phaseId, memberId } = useRequiredParams<{
    gameId: string;
    phaseId: string;
    memberId: string;
  }>();

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <GameDetailAppBar
        title="Report player"
        variant="secondary"
        onNavigateBack={() =>
          navigate(`/game/${gameId}/phase/${phaseId}/member/${memberId}`)
        }
      />
      <div className="flex-1 overflow-y-auto">
        <Panel>
          <Panel.Content className="flex flex-col gap-4 px-3 py-4 md:p-2">
            <div className="flex flex-col gap-2 text-sm text-muted-foreground">
              <p>
                Reports are confidential. The reported player isn't told who
                reported them, and the moderation team checks every report.
                Approved reports appear on the player's profile.
              </p>
              <p>
                Only report breaches of the{" "}
                <Link to="/code-of-conduct" className="text-primary hover:underline">
                  Code of Conduct
                </Link>
                .
              </p>
            </div>
            <QueryErrorBoundary>
              <Suspense fallback={<ReportMemberFormSkeleton />}>
                <ReportMemberForm />
              </Suspense>
            </QueryErrorBoundary>
          </Panel.Content>
        </Panel>
      </div>
    </div>
  );
};

export { ReportMemberScreen };
