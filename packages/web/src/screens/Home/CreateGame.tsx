import React, { Suspense, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useForm, Control } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Calendar,
  Check,
  Clock,
  Lock,
  Map,
  MessageSquare,
  MessageSquareOff,
  Monitor,
  Timer,
  User,
  Users,
} from "lucide-react";
import { toast } from "sonner";

import { Alert, AlertDescription } from "@/components/ui/alert";

import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

import { cn } from "@/lib/utils";
import { randomGameName } from "@/util";
import { ExpandableMapPreview } from "@/components/ExpandableMapPreview";
import { DeadlineSummary } from "@/components/DeadlineSummary";
import {
  DURATION_OPTIONS,
  DURATION_ENUM_VALUES,
  FREQUENCY_OPTIONS,
  TIMEZONE_OPTIONS,
  NMR_EXTENSION_OPTIONS,
  MIN_RELIABILITY_OPTIONS,
} from "@/constants";
import {
  useVariantsListSuspense,
  useGameCreate,
  useSandboxGameCreate,
  getGamesFindSimilarRetrieveQueryOptions,
  GameList,
  Variant,
  NationAssignmentEnum,
} from "@/api/generated/endpoints";
import { useQueryClient } from "@tanstack/react-query";
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
import { useCheckNotificationPermission } from "@/hooks/useCheckNotificationPermission";
import { CREATE_GAME_PARAM } from "@/utils/routes";

const gameSchema = z.object({
  name: z
    .string()
    .min(1, "Game name is required")
    .max(100, "Game name must be less than 100 characters"),
  variantId: z.string().min(1, "Please select a variant"),
  mode: z.enum(["standard", "gunboat", "sandbox"] as const),
  nationAssignment: z.enum(["random", "ordered"] as const),
  private: z.boolean(),
  gameMaster: z.boolean(),
  deadlineMode: z.enum(["duration", "fixed_time"] as const),
  movementPhaseDuration: z.enum(DURATION_ENUM_VALUES).optional(),
  retreatPhaseDuration: z.enum(DURATION_ENUM_VALUES).optional().nullable(),
  fixedDeadlineTime: z.string().optional().nullable(),
  fixedDeadlineTimezone: z.string().optional().nullable(),
  movementFrequency: z
    .enum(["hourly", "daily", "every_2_days", "weekly"] as const)
    .optional()
    .nullable(),
  retreatFrequency: z
    .enum(["hourly", "daily", "every_2_days", "weekly"] as const)
    .optional()
    .nullable(),
  nmrExtensionsAllowed: z.enum(["0", "1", "2"] as const),
  minReliability: z.enum([
    "open",
    "reliable_and_new",
    "reliable_only",
  ] as const),
});

type GameFormValues = z.infer<typeof gameSchema>;
type GameMode = GameFormValues["mode"];

const modeToBackendFields = (mode: "standard" | "gunboat") =>
  ({
    anonymous: mode === "gunboat",
    pressType: mode === "gunboat" ? "no_press" : "full_press",
  }) as const;

interface RadioCardOption<T extends string> {
  value: T;
  label: string;
  description?: string;
  icon?: React.ReactNode;
}

interface RadioCardsProps<T extends string> {
  options: RadioCardOption<T>[];
  value: T;
  onChange: (value: T) => void;
  disabled?: boolean;
  columns?: number;
}

const RadioCards = <T extends string>({
  options,
  value,
  onChange,
  disabled,
  columns,
}: RadioCardsProps<T>) => (
  <RadioGroup
    value={value}
    onValueChange={next => onChange(next as T)}
    disabled={disabled}
    style={
      columns
        ? { gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }
        : undefined
    }
  >
    {options.map(option => {
      const id = `radio-card-${option.value}`;
      const selected = value === option.value;
      return (
        <Label
          key={option.value}
          htmlFor={id}
          className={cn(
            "flex items-start gap-3 rounded-lg border p-3 cursor-pointer transition-colors",
            selected
              ? "border-primary bg-primary/5"
              : "border-input hover:border-muted-foreground/50",
            disabled && "cursor-not-allowed opacity-50 hover:border-input"
          )}
        >
          <RadioGroupItem value={option.value} id={id} className="mt-0.5" />
          {option.icon ? (
            <span className={selected ? "text-primary" : "text-muted-foreground"}>
              {option.icon}
            </span>
          ) : null}
          <div className="space-y-1">
            <p className="text-sm font-medium leading-none">{option.label}</p>
            {option.description ? (
              <p className="text-sm text-muted-foreground">{option.description}</p>
            ) : null}
          </div>
        </Label>
      );
    })}
  </RadioGroup>
);

interface MetadataRow {
  label: string;
  value?: string | React.ReactNode;
  text?: string;
  icon?: React.ReactNode;
}

interface GameMetadataTableProps {
  rows: MetadataRow[];
}

const GameMetadataTable: React.FC<GameMetadataTableProps> = ({ rows }) => {
  return (
    <div className="divide-y border rounded-lg">
      {rows.map((row, index) =>
        row.text ? (
          <div key={index} className="p-4">
            <div className="flex items-center gap-3 mb-1">
              {row.icon}
              <span className="text-sm">{row.label}</span>
            </div>
            <p className="text-sm text-muted-foreground whitespace-pre-line pl-7">
              {row.text}
            </p>
          </div>
        ) : (
          <div key={index} className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              {row.icon}
              <span className="text-sm">{row.label}</span>
            </div>
            <span className="text-sm text-muted-foreground">{row.value}</span>
          </div>
        )
      )}
    </div>
  );
};

interface VariantSelectorProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  control: Control<any>;
  name: string;
  disabled?: boolean;
  variants: Variant[];
  selectedVariant?: Variant;
}

const VariantSelector: React.FC<VariantSelectorProps> = ({
  control,
  name,
  disabled,
  variants,
  selectedVariant,
}) => {
  return (
    <div className="space-y-4">
      <FormField
        control={control}
        name={name}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Variant</FormLabel>
            <Select
              onValueChange={field.onChange}
              value={field.value}
              disabled={disabled}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a variant" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {variants?.map(variant => (
                  <SelectItem key={variant.id} value={variant.id}>
                    {variant.name} ({variant.nations.length} players)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />

      {selectedVariant?.templatePhase ? (
        <ExpandableMapPreview
          variant={selectedVariant}
          phase={selectedVariant.templatePhase}
          style={{ width: "100%", height: "100%" }}
        />
      ) : null}

      <GameMetadataTable
        rows={[
          {
            label: "Number of nations",
            value: selectedVariant?.nations.length.toString(),
            icon: <Users className="size-4" />,
          },
          {
            label: "Start year",
            value: selectedVariant?.templatePhase.year.toString(),
            icon: <Calendar className="size-4" />,
          },
          {
            label: "Original author",
            value: selectedVariant?.author,
            icon: <User className="size-4" />,
          },
          ...(selectedVariant?.description
            ? [
                {
                  label: "Description",
                  text: selectedVariant.description,
                  icon: <Map className="size-4" />,
                },
              ]
            : []),
          ...(selectedVariant?.rules
            ? [
                {
                  label: "Rules",
                  text: selectedVariant.rules,
                  icon: <BookOpen className="size-4" />,
                },
              ]
            : []),
        ]}
      />
    </div>
  );
};

function getBrowserTimezone(): string {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const validTimezones = TIMEZONE_OPTIONS.map(
    o => o.value
  ) as readonly string[];
  return validTimezones.includes(tz) ? tz : "America/New_York";
}

const STEPS = ["General", "Deadlines", "Advanced"] as const;

const STEP_FIELDS: Record<number, (keyof GameFormValues)[]> = {
  0: ["name", "variantId", "mode", "private", "gameMaster"],
  1: [
    "deadlineMode",
    "movementPhaseDuration",
    "retreatPhaseDuration",
    "fixedDeadlineTime",
    "fixedDeadlineTimezone",
    "movementFrequency",
    "retreatFrequency",
  ],
  2: ["nmrExtensionsAllowed", "minReliability"],
};

interface StepperStep {
  label: string;
  disabled?: boolean;
}

interface StepperProps {
  steps: readonly StepperStep[];
  currentStep: number;
}

const Stepper: React.FC<StepperProps> = ({ steps, currentStep }) => (
  <div className="flex items-center">
    {steps.map((step, index) => {
      const isComplete = !step.disabled && index < currentStep;
      const isCurrent = !step.disabled && index === currentStep;
      return (
        <React.Fragment key={step.label}>
          <div
            className={cn(
              "flex items-center gap-2",
              step.disabled && "opacity-50"
            )}
          >
            <div
              className={cn(
                "flex size-7 items-center justify-center rounded-full border text-sm font-medium",
                isComplete &&
                  "border-primary bg-primary text-primary-foreground",
                isCurrent && "border-primary text-primary",
                !isComplete &&
                  !isCurrent &&
                  "border-muted-foreground/30 text-muted-foreground"
              )}
            >
              {isComplete ? <Check className="size-4" /> : index + 1}
            </div>
            <span
              className={cn(
                "text-sm font-medium",
                isCurrent ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {step.label}
            </span>
          </div>
          {index < steps.length - 1 && (
            <div
              className={cn(
                "mx-3 h-px flex-1",
                index < currentStep ? "bg-primary" : "bg-border"
              )}
            />
          )}
        </React.Fragment>
      );
    })}
  </div>
);

interface CreateGameFormProps {
  onStandardSubmit: (data: GameFormValues) => Promise<void>;
  onSandboxSubmit: (data: GameFormValues) => Promise<void>;
  isSubmitting: boolean;
  variants: Variant[];
  initialVariantId?: string;
  initialPrivate?: boolean;
  initialMode?: GameMode;
}

const CreateGameForm: React.FC<CreateGameFormProps> = ({
  onStandardSubmit,
  onSandboxSubmit,
  isSubmitting,
  variants,
  initialVariantId,
  initialPrivate,
  initialMode,
}) => {
  const form = useForm<GameFormValues>({
    resolver: zodResolver(gameSchema),
    defaultValues: {
      name: randomGameName(),
      variantId: initialVariantId ?? variants[0]?.id ?? "",
      mode: initialMode ?? "standard",
      nationAssignment: "random" as NationAssignmentEnum,
      private: initialPrivate ?? false,
      gameMaster: false,
      deadlineMode: "fixed_time",
      movementPhaseDuration: "24 hours",
      retreatPhaseDuration: null,
      fixedDeadlineTime: "21:00",
      fixedDeadlineTimezone: getBrowserTimezone(),
      movementFrequency: "daily",
      retreatFrequency: null,
      nmrExtensionsAllowed: "0",
      minReliability: "open",
    },
  });

  const [step, setStep] = useState(0);

  const selectedVariant = variants?.find(v => v.id === form.watch("variantId"));
  const deadlineMode = form.watch("deadlineMode");
  const isPrivate = form.watch("private");
  const isSandbox = form.watch("mode") === "sandbox";
  const lastStep = isSandbox ? 0 : STEPS.length - 1;
  const isInitialVariantDraft =
    initialVariantId !== undefined &&
    variants.find(v => v.id === initialVariantId)?.status === "draft";

  const stepperSteps: StepperStep[] = STEPS.map((label, index) => ({
    label,
    disabled: isSandbox && index > 0,
  }));

  const handleNext = async () => {
    const valid = await form.trigger(STEP_FIELDS[step]);
    if (valid) {
      setStep(s => Math.min(s + 1, lastStep));
    }
  };

  const handleBack = () => setStep(s => Math.max(s - 1, 0));

  const handleFormSubmit = form.handleSubmit(async data => {
    if (step < lastStep) {
      await handleNext();
      return;
    }
    if (data.mode === "sandbox") {
      await onSandboxSubmit(data);
    } else {
      await onStandardSubmit(data);
    }
  });

  return (
    <Form {...form}>
      <form onSubmit={handleFormSubmit} className="space-y-6">
        <Stepper steps={stepperSteps} currentStep={step} />

        {step === 0 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">General</h2>

            <FormField
              control={form.control}
              name="mode"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Mode</FormLabel>
                  <RadioCards
                    value={field.value}
                    onChange={value => {
                      field.onChange(value);
                      if (value === "sandbox") {
                        form.setValue("private", false);
                        form.setValue("gameMaster", false);
                      }
                    }}
                    disabled={isSubmitting}
                    options={[
                      {
                        value: "standard",
                        label: "Standard",
                        description:
                          "Play against other people. Talk to anyone, form alliances, and negotiate freely.",
                        icon: <MessageSquare className="size-5" />,
                      },
                      {
                        value: "gunboat",
                        label: "Gunboat",
                        description:
                          "Play against other people with no messaging. Player names are hidden — only the moves on the board tell you who to trust.",
                        icon: <MessageSquareOff className="size-5" />,
                      },
                      {
                        value: "sandbox",
                        label: "Sandbox",
                        description:
                          "Practise on your own by controlling every nation. No deadlines — resolve each phase whenever you're ready.",
                        icon: <Monitor className="size-5" />,
                      },
                    ]}
                  />
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Game Name</FormLabel>
                  <FormControl>
                    <Input {...field} disabled={isSubmitting} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="private"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={checked => {
                        field.onChange(checked);
                        if (!checked) {
                          form.setValue("gameMaster", false);
                        }
                      }}
                      disabled={
                        isSubmitting || isInitialVariantDraft || isSandbox
                      }
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel className="flex items-center gap-1.5">
                      <Lock className="size-3.5" />
                      Private
                    </FormLabel>
                    <FormDescription>
                      Hidden from public listings. Only people you share the
                      direct link with can find and join the game.
                    </FormDescription>
                  </div>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="gameMaster"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                      disabled={isSubmitting || !isPrivate || isSandbox}
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel>Game Master</FormLabel>
                    <FormDescription>
                      Run this game as a non-playing Game Master. You won't take
                      a nation, but you can pause the game, extend deadlines,
                      and remove players. Only available in private games.
                    </FormDescription>
                  </div>
                </FormItem>
              )}
            />

            <hr className="border-t" />

            <VariantSelector
              control={form.control}
              name="variantId"
              disabled={isSubmitting || isInitialVariantDraft}
              variants={variants}
              selectedVariant={selectedVariant}
            />
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Deadlines</h2>

            <FormField
              control={form.control}
              name="deadlineMode"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Deadline type</FormLabel>
                  <RadioCards
                    columns={2}
                    value={field.value}
                    onChange={field.onChange}
                    disabled={isSubmitting}
                    options={[
                      {
                        value: "fixed_time",
                        label: "Fixed time",
                        icon: <Clock className="size-5" />,
                      },
                      {
                        value: "duration",
                        label: "Duration",
                        icon: <Timer className="size-5" />,
                      },
                    ]}
                  />
                  <FormDescription>
                    {field.value === "fixed_time"
                      ? "Every phase resolves at the same time of day (for example 9pm). Predictable, but a phase always runs for its full length even when everyone is ready."
                      : "Every phase lasts a fixed length of time from when it starts (for example 24 hours), and can resolve early once all players confirm their orders — so the game can move faster."}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {deadlineMode === "duration" && (
              <div className="grid w-full grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="movementPhaseDuration"
                  render={({ field: durationField }) => (
                    <FormItem>
                      <FormLabel>Movement</FormLabel>
                      <Select
                        onValueChange={durationField.onChange}
                        value={durationField.value}
                        disabled={isSubmitting}
                      >
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {DURATION_OPTIONS.map(option => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="retreatPhaseDuration"
                  render={({ field: retreatField }) => (
                    <FormItem>
                      <FormLabel>Retreat/Adjustment</FormLabel>
                      <Select
                        onValueChange={retreatField.onChange}
                        value={retreatField.value ?? undefined}
                        disabled={isSubmitting}
                      >
                        <FormControl>
                          <SelectTrigger className="w-full min-w-0 [&>[data-slot=select-value]]:min-w-0">
                            <SelectValue placeholder="Same as movement" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {DURATION_OPTIONS.map(option => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {deadlineMode === "fixed_time" && (
              <>
                <div className="grid w-full grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="fixedDeadlineTime"
                    render={({ field: timeField }) => (
                      <FormItem>
                        <FormLabel>Time</FormLabel>
                        <FormControl>
                          <Input
                            type="time"
                            className="appearance-none"
                            value={timeField.value ?? ""}
                            onChange={timeField.onChange}
                            disabled={isSubmitting}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="fixedDeadlineTimezone"
                    render={({ field: tzField }) => (
                      <FormItem>
                        <FormLabel>Timezone</FormLabel>
                        <Select
                          onValueChange={tzField.onChange}
                          value={tzField.value ?? undefined}
                          disabled={isSubmitting}
                        >
                          <FormControl>
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {TIMEZONE_OPTIONS.map(option => (
                              <SelectItem key={option.value} value={option.value}>
                                {option.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="grid w-full grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="movementFrequency"
                    render={({ field: freqField }) => (
                      <FormItem>
                        <FormLabel>Movement</FormLabel>
                        <Select
                          onValueChange={freqField.onChange}
                          value={freqField.value ?? undefined}
                          disabled={isSubmitting}
                        >
                          <FormControl>
                            <SelectTrigger className="w-full">
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {FREQUENCY_OPTIONS.map(option => (
                              <SelectItem key={option.value} value={option.value}>
                                {option.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="retreatFrequency"
                    render={({ field: retreatFreqField }) => (
                      <FormItem>
                        <FormLabel>Retreat/Adjustment</FormLabel>
                        <Select
                          onValueChange={retreatFreqField.onChange}
                          value={retreatFreqField.value ?? undefined}
                          disabled={isSubmitting}
                        >
                          <FormControl>
                            <SelectTrigger className="w-full min-w-0 [&>[data-slot=select-value]]:min-w-0">
                              <SelectValue placeholder="Same as movement" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {FREQUENCY_OPTIONS.map(option => (
                              <SelectItem key={option.value} value={option.value}>
                                {option.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </>
            )}

            <Alert className="mt-4">
              <Clock className="h-4 w-4" />
              <AlertDescription>
                <DeadlineSummary
                  game={{
                    movementPhaseDuration:
                      form.watch("movementPhaseDuration") ?? null,
                    retreatPhaseDuration:
                      form.watch("retreatPhaseDuration") ?? null,
                    deadlineMode,
                    fixedDeadlineTime: form.watch("fixedDeadlineTime") ?? null,
                    fixedDeadlineTimezone:
                      form.watch("fixedDeadlineTimezone") ?? null,
                    movementFrequency: form.watch("movementFrequency") ?? null,
                    retreatFrequency: form.watch("retreatFrequency") ?? null,
                  }}
                />
              </AlertDescription>
            </Alert>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Advanced</h2>

            <FormField
              control={form.control}
              name="nmrExtensionsAllowed"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Automatic extensions</FormLabel>
                  <RadioCards
                    columns={NMR_EXTENSION_OPTIONS.length}
                    value={field.value}
                    onChange={field.onChange}
                    disabled={isSubmitting}
                    options={NMR_EXTENSION_OPTIONS.map(option => ({
                      value: option.value,
                      label: option.label,
                    }))}
                  />
                  <FormDescription>
                    When a player misses a deadline, an automatic extension gives
                    them more time instead of resolving the phase without their
                    orders. This sets how many extensions each player gets before
                    a missed deadline counts against them.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="minReliability"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Player reliability</FormLabel>
                  <RadioCards
                    value={field.value}
                    onChange={field.onChange}
                    disabled={isSubmitting}
                    options={MIN_RELIABILITY_OPTIONS.map(option => ({
                      value: option.value,
                      label: option.label,
                      description: option.description,
                    }))}
                  />
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        )}

        <div className="flex gap-3">
          {step > 0 && (
            <Button
              type="button"
              variant="outline"
              onClick={handleBack}
              disabled={isSubmitting}
              className="flex-1"
            >
              <ArrowLeft />
              Back
            </Button>
          )}
          {step < lastStep ? (
            <Button
              key="next"
              type="button"
              onClick={handleNext}
              className="flex-1"
            >
              Next
              <ArrowRight />
            </Button>
          ) : (
            <Button
              key="submit"
              type="button"
              onClick={() => handleFormSubmit()}
              className="flex-1"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Creating..." : "Create Game"}
            </Button>
          )}
        </div>
      </form>
    </Form>
  );
};

const CreateGame: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { data: allVariants } = useVariantsListSuspense();
  const publishedVariants = React.useMemo(
    () => allVariants.filter(v => v.status === "published"),
    [allVariants]
  );

  const initialVariantId =
    searchParams.get(CREATE_GAME_PARAM.variantId) ?? undefined;
  const initialPrivate = searchParams.get(CREATE_GAME_PARAM.private) === "true";
  const initialMode: GameMode =
    searchParams.get("sandbox") === "true" ? "sandbox" : "standard";

  const initialVariant = React.useMemo(
    () =>
      initialVariantId
        ? allVariants.find(v => v.id === initialVariantId)
        : undefined,
    [allVariants, initialVariantId]
  );
  const variants = React.useMemo(() => {
    if (
      initialVariant &&
      !publishedVariants.some(v => v.id === initialVariant.id)
    ) {
      return [initialVariant, ...publishedVariants];
    }
    return publishedVariants;
  }, [publishedVariants, initialVariant]);
  const createGameMutation = useGameCreate();
  const createSandboxGameMutation = useSandboxGameCreate();
  const checkNotificationPermission = useCheckNotificationPermission();

  const [similarMatch, setSimilarMatch] = useState<GameList | null>(null);
  const [pendingFormData, setPendingFormData] = useState<GameFormValues | null>(
    null
  );

  const submitCreateGame = async (data: GameFormValues) => {
    try {
      const formattedTime = data.fixedDeadlineTime
        ? `${data.fixedDeadlineTime}:00`
        : null;

      const game = await createGameMutation.mutateAsync({
        data: {
          name: data.name,
          variantId: data.variantId,
          nationAssignment: data.nationAssignment,
          private: data.private,
          gameMaster: data.gameMaster,
          ...modeToBackendFields(
            data.mode === "gunboat" ? "gunboat" : "standard"
          ),
          deadlineMode: data.deadlineMode,
          movementPhaseDuration:
            data.deadlineMode === "duration"
              ? data.movementPhaseDuration
              : undefined,
          retreatPhaseDuration:
            data.deadlineMode === "duration"
              ? data.retreatPhaseDuration
              : undefined,
          fixedDeadlineTime:
            data.deadlineMode === "fixed_time" ? formattedTime : null,
          fixedDeadlineTimezone:
            data.deadlineMode === "fixed_time"
              ? data.fixedDeadlineTimezone
              : null,
          movementFrequency:
            data.deadlineMode === "fixed_time" ? data.movementFrequency : null,
          retreatFrequency:
            data.deadlineMode === "fixed_time" ? data.retreatFrequency : null,
          nmrExtensionsAllowed: parseInt(data.nmrExtensionsAllowed, 10),
          minReliability: data.minReliability,
        },
      });
      toast.success("Game created successfully");
      checkNotificationPermission();
      navigate(`/game-info/${game.id}`);
    } catch {
      toast.error("Failed to create game");
    }
  };

  const handleStandardGameSubmit = async (data: GameFormValues) => {
    const skipSimilarCheck =
      data.private ||
      data.deadlineMode !== "duration" ||
      !data.movementPhaseDuration;

    if (!skipSimilarCheck) {
      try {
        const result = await queryClient.fetchQuery(
          getGamesFindSimilarRetrieveQueryOptions({
            variant: data.variantId,
            movement_phase_duration: data.movementPhaseDuration as string,
          })
        );
        if (result.game) {
          setSimilarMatch(result.game);
          setPendingFormData(data);
          return;
        }
      } catch {
        // Fall through to create on lookup failure — don't block the user.
      }
    }

    await submitCreateGame(data);
  };

  const handleSimilarMatchContinue = async () => {
    const data = pendingFormData;
    setSimilarMatch(null);
    setPendingFormData(null);
    if (data) {
      await submitCreateGame(data);
    }
  };

  const handleSimilarMatchJoin = () => {
    if (similarMatch) {
      navigate(`/game-info/${similarMatch.id}`);
    }
    setSimilarMatch(null);
    setPendingFormData(null);
  };

  const handleSandboxGameSubmit = async (data: GameFormValues) => {
    try {
      const game = await createSandboxGameMutation.mutateAsync({
        data: { name: data.name, variantId: data.variantId },
      });
      toast.success("Sandbox game created successfully");
      navigate(`/game/${game.id}`);
    } catch {
      toast.error("Failed to create sandbox game");
    }
  };

  const matchedVariant = similarMatch
    ? variants.find(v => v.id === similarMatch.variantId)
    : null;

  return (
    <div className="space-y-4">
      <ScreenCard>
        <ScreenCardContent>
          <CreateGameForm
            onStandardSubmit={handleStandardGameSubmit}
            onSandboxSubmit={handleSandboxGameSubmit}
            isSubmitting={
              createGameMutation.isPending ||
              createSandboxGameMutation.isPending
            }
            variants={variants}
            initialVariantId={initialVariantId}
            initialPrivate={initialPrivate}
            initialMode={initialMode}
          />
        </ScreenCardContent>
      </ScreenCard>

      <AlertDialog
        open={similarMatch !== null}
        onOpenChange={open => {
          if (!open) {
            setSimilarMatch(null);
            setPendingFormData(null);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              A similar game is already forming
            </AlertDialogTitle>
            <AlertDialogDescription>
              Join it instead to start playing sooner.
            </AlertDialogDescription>
          </AlertDialogHeader>
          {similarMatch && (
            <div className="space-y-1 text-sm">
              <p className="font-semibold">{similarMatch.name}</p>
              <p className="text-muted-foreground">
                {similarMatch.members.length}
                {matchedVariant
                  ? ` / ${matchedVariant.nations.length}`
                  : ""}{" "}
                players
              </p>
            </div>
          )}
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleSimilarMatchContinue}>
              Continue
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleSimilarMatchJoin}>
              Join Them?
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

const CreateGameSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Create Game" />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <CreateGame />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { CreateGameSuspense as CreateGame, modeToBackendFields };
export type { CreateGameFormProps };
