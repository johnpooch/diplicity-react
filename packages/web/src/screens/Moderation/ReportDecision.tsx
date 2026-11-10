import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { PrimaryButton, SecondaryButton } from "@/components/ui/role-buttons";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  ModerationReportActionKeyEnum,
  ReasonEnum,
  getModerationReportsListQueryKey,
  getModerationReportsRetrieveQueryKey,
  useModerationReportsApproveCreate,
  useModerationReportsRejectCreate,
  useReportReasonsListSuspense,
} from "@/api/generated/endpoints";
import type { ModerationReportOutput } from "@/api/generated/endpoints";

const NOTE_MAX_LENGTH = 1000;

const decisionSchema = z.object({
  reason: z.nativeEnum(ReasonEnum),
  note: z
    .string()
    .trim()
    .max(
      NOTE_MAX_LENGTH,
      `Notes cannot be longer than ${NOTE_MAX_LENGTH} characters.`
    ),
});

type DecisionFormValues = z.infer<typeof decisionSchema>;

type Decision =
  | typeof ModerationReportActionKeyEnum.approve
  | typeof ModerationReportActionKeyEnum.reject;

interface ReportDecisionProps {
  report: ModerationReportOutput;
  reportedName: string;
}

const ReportDecision: React.FC<ReportDecisionProps> = ({
  report,
  reportedName,
}) => {
  const queryClient = useQueryClient();
  const { data: reasons } = useReportReasonsListSuspense();
  const approveMutation = useModerationReportsApproveCreate();
  const rejectMutation = useModerationReportsRejectCreate();
  const [pending, setPending] = useState<Decision | null>(null);

  const form = useForm<DecisionFormValues>({
    resolver: zodResolver(decisionSchema),
    defaultValues: { reason: report.reason, note: "" },
  });

  const selectedReason = form.watch("reason");
  const reasonLabel =
    reasons.find(reason => reason.key === selectedReason)?.label ??
    selectedReason;

  const decisions = {
    [ModerationReportActionKeyEnum.approve]: {
      label: "Approve",
      title: "Approve this report?",
      description: `Decisions are final. ${reportedName} gets a mark for ${reasonLabel} in this game.`,
      failure: "Failed to approve report",
      mutation: approveMutation,
      data: (values: DecisionFormValues) => values,
    },
    [ModerationReportActionKeyEnum.reject]: {
      label: "Reject",
      title: "Reject this report?",
      description: `Decisions are final. Nothing is added to ${reportedName}'s profile.`,
      failure: "Failed to reject report",
      mutation: rejectMutation,
      data: ({ note }: DecisionFormValues) => ({ note }),
    },
  };

  const available = report.actions.some(
    action => action.key in decisions && action.blockedReason === null
  );

  if (!available) {
    return null;
  }

  const handleDecide = async (
    decision: Decision,
    values: DecisionFormValues
  ) => {
    try {
      await decisions[decision].mutation.mutateAsync({
        id: report.id,
        data: decisions[decision].data(values),
      });
    } catch {
      toast.error(decisions[decision].failure);
    }
    queryClient.invalidateQueries({
      queryKey: getModerationReportsListQueryKey(),
    });
    queryClient.invalidateQueries({
      queryKey: getModerationReportsRetrieveQueryKey(report.id),
    });
  };

  const handleConfirm = () => {
    const decision = pending;
    if (decision === null) return;
    form.handleSubmit(values => handleDecide(decision, values))();
  };

  const isSubmitting = approveMutation.isPending || rejectMutation.isPending;
  const confirmation = pending ? decisions[pending] : null;

  return (
    <Form {...form}>
      <div className="flex flex-col gap-4">
        <FormField
          control={form.control}
          name="reason"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Mark reason</FormLabel>
              <FormControl>
                <Card className="overflow-hidden py-0">
                  <CardContent className="p-0">
                    <RadioGroup
                      value={field.value}
                      onValueChange={field.onChange}
                      disabled={isSubmitting}
                      className="gap-0 divide-y"
                    >
                      {reasons.map(reason => (
                        <label
                          key={reason.key}
                          className="flex cursor-pointer items-center gap-3 p-3 hover:bg-accent/50"
                        >
                          <RadioGroupItem value={reason.key} />
                          <span className="text-sm">{reason.label}</span>
                        </label>
                      ))}
                    </RadioGroup>
                  </CardContent>
                </Card>
              </FormControl>
              <FormDescription>
                Change this if the reporter picked the wrong reason.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="note"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Moderator's note</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Why did you decide this way? (optional)"
                  maxLength={NOTE_MAX_LENGTH}
                  disabled={isSubmitting}
                  {...field}
                />
              </FormControl>
              <FormDescription>Only moderators see this note.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <div className="flex justify-end gap-2">
          <SecondaryButton
            type="button"
            disabled={isSubmitting}
            onClick={form.handleSubmit(() =>
              setPending(ModerationReportActionKeyEnum.reject)
            )}
          >
            Reject
          </SecondaryButton>
          <PrimaryButton
            type="button"
            disabled={isSubmitting}
            onClick={form.handleSubmit(() =>
              setPending(ModerationReportActionKeyEnum.approve)
            )}
          >
            Approve
          </PrimaryButton>
        </div>
      </div>
      <AlertDialog
        open={confirmation !== null}
        onOpenChange={open => !open && setPending(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmation?.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmation?.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirm}>
              {confirmation?.label}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Form>
  );
};

export { ReportDecision };
