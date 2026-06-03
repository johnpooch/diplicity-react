import React, { Suspense, useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useForm, Control } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  BookOpen,
  Calendar,
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

import { CardDescription } from "@/components/ui/card";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

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

import { randomGameName } from "@/util";
import { MapPreview } from "@/components/MapPreview";
import { DeadlineSummary } from "@/components/DeadlineSummary";
import {
  DURATION_OPTIONS,
  DURATION_ENUM_VALUES,
  FREQUENCY_OPTIONS,
  TIMEZONE_OPTIONS,
  NMR_EXTENSION_OPTIONS,
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

const standardGameSchema = z.object({
  name: z
    .string()
    .min(1, "Game name is required")
    .max(100, "Game name must be less than 100 characters"),
  variantId: z.string().min(1, "Please select a variant"),
  mode: z.enum(["standard", "gunboat"] as const),
  nationAssignment: z.enum(["random", "ordered"] as const),
  private: z.boolean(),
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
});

const sandboxGameSchema = z.object({
  sandboxGame: z.object({
    name: z
      .string()
      .min(1, "Game name is required")
      .max(100, "Game name must be less than 100 characters"),
    variantId: z.string().min(1, "Please select a variant"),
  }),
});

type StandardGameFormValues = z.infer<typeof standardGameSchema>;
type SandboxGameFormValues = z.infer<typeof sandboxGameSchema>;

const modeToBackendFields = (mode: StandardGameFormValues["mode"]) => ({
  anonymous: mode === "gunboat",
  pressType: mode === "gunboat" ? "no_press" : "full_press",
} as const);

interface RadioCardOption<T extends string> {
  value: T;
  label: string;
  icon?: React.ReactNode;
}

interface RadioCardGroupProps<T extends string> {
  options: RadioCardOption<T>[];
  value: T;
  onChange: (value: T) => void;
  disabled?: boolean;
  size?: "default" | "large";
}

const RadioCardGroup = <T extends string>({
  options,
  value,
  onChange,
  disabled,
  size = "default",
}: RadioCardGroupProps<T>) => {
  return (
    <div
      className="grid gap-x-2 gap-y-0.5"
      style={{ gridTemplateColumns: `repeat(${options.length}, 1fr)` }}
    >
      {options.map(option => (
        <button
          key={option.value}
          type="button"
          onClick={() => !disabled && onChange(option.value)}
          className={cn(
            "flex flex-col items-center gap-2 rounded-lg border-2 cursor-pointer transition-colors",
            size === "large" ? "px-4 py-1" : "px-3 py-1",
            value === option.value
              ? "border-primary bg-primary/5 text-primary"
              : "border-border text-muted-foreground hover:border-muted-foreground hover:text-foreground",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          {option.icon}
          <span className={cn("font-medium", size === "large" ? "text-base" : "text-sm")}>
            {option.label}
          </span>
        </button>
      ))}
    </div>
  );
};

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
            <p className="text-sm text-muted-foreground whitespace-pre-line pl-7">{row.text}</p>
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
            <Select
              onValueChange={field.onChange}
              value={field.value}
              disabled={disabled}
            >
              <FormControl>
                <SelectTrigger>
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
        <MapPreview
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
          ...(selectedVariant?.description ? [{
            label: "Description",
            text: selectedVariant.description,
            icon: <Map className="size-4" />,
          }] : []),
          ...(selectedVariant?.rules ? [{
            label: "Rules",
            text: selectedVariant.rules,
            icon: <BookOpen className="size-4" />,
          }] : []),
        ]}
      />
    </div>
  );
};

function getBrowserTimezone(): string {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const validTimezones = TIMEZONE_OPTIONS.map(o => o.value) as readonly string[];
  return validTimezones.includes(tz) ? tz : "America/New_York";
}

interface CreateStandardGameFormProps {
  onSubmit: (data: StandardGameFormValues) => Promise<void>;
  isSubmitting: boolean;
  variants: Variant[];
}

const CreateStandardGameForm: React.FC<CreateStandardGameFormProps> = ({
  onSubmit,
  isSubmitting,
  variants,
}) => {
  const form = useForm<StandardGameFormValues>({
    resolver: zodResolver(standardGameSchema),
    defaultValues: {
      name: randomGameName(),
      variantId: variants[0].id,
      mode: "standard",
      nationAssignment: "random" as NationAssignmentEnum,
      private: false,
      deadlineMode: "fixed_time",
      movementPhaseDuration: "24 hours",
      retreatPhaseDuration: null,
      fixedDeadlineTime: "21:00",
      fixedDeadlineTimezone: getBrowserTimezone(),
      movementFrequency: "daily",
      retreatFrequency: null,
      nmrExtensionsAllowed: "0",
    },
  });

  const selectedVariant = variants?.find(v => v.id === form.watch("variantId"));
  const deadlineMode = form.watch("deadlineMode");

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="mode"
          render={({ field }) => (
            <FormItem className="space-y-3">
              <RadioCardGroup
                options={[
                  {
                    value: "standard" as const,
                    label: "Full press",
                    icon: <MessageSquare className="size-5" />,
                  },
                  {
                    value: "gunboat" as const,
                    label: "Gunboat (no press)",
                    icon: <MessageSquareOff className="size-5" />,
                  },
                ]}
                value={field.value}
                onChange={field.onChange}
                disabled={isSubmitting}
              />
              <FormMessage />
            </FormItem>
          )}
        />

        <hr className="border-t" />

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">General</h2>

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
                    onCheckedChange={field.onChange}
                    disabled={isSubmitting}
                  />
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel className="flex items-center gap-1.5">
                    <Lock className="h-3 w-3" />
                    Private
                  </FormLabel>
                  <FormDescription>
                    Private games are hidden from public listings and only accessible via direct link that can be shared.
                  </FormDescription>
                </div>
              </FormItem>
            )}
          />
        </div>

        <hr className="border-t" />

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Deadlines</h2>

          <FormField
            control={form.control}
            name="deadlineMode"
            render={({ field }) => (
              <FormItem className="space-y-3">
                <RadioCardGroup
                  options={[
                    {
                      value: "fixed_time" as const,
                      label: "Fixed time",
                      icon: <Clock className="size-5" />,
                    },
                    {
                      value: "duration" as const,
                      label: "Duration",
                      icon: <Timer className="size-5" />,
                    },
                  ]}
                  value={field.value}
                  onChange={field.onChange}
                  disabled={isSubmitting}
                />
                <p className="text-sm text-muted-foreground">
                  {field.value === "fixed_time"
                    ? "Deadlines are always at the fixed time, phases are always the same length."
                    : "Phases can resolve earlier if all players confirm their orders, meaning the deadline time can shift."}
                </p>
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
                          <SelectItem
                            key={option.value}
                            value={option.value}
                          >
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
                          <SelectItem
                            key={option.value}
                            value={option.value}
                          >
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
                            <SelectItem
                              key={option.value}
                              value={option.value}
                            >
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
                            <SelectItem
                              key={option.value}
                              value={option.value}
                            >
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
                            <SelectItem
                              key={option.value}
                              value={option.value}
                            >
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
                  fixedDeadlineTime:
                    form.watch("fixedDeadlineTime") ?? null,
                  fixedDeadlineTimezone:
                    form.watch("fixedDeadlineTimezone") ?? null,
                  movementFrequency:
                    form.watch("movementFrequency") ?? null,
                  retreatFrequency:
                    form.watch("retreatFrequency") ?? null,
                }}
              />
            </AlertDescription>
          </Alert>
        </div>

        <hr className="border-t" />

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Variant</h2>

          <VariantSelector
            control={form.control}
            name="variantId"
            disabled={isSubmitting}
            variants={variants}
            selectedVariant={selectedVariant}
          />
        </div>

        <hr className="border-t" />

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Advanced</h2>

          <FormField
            control={form.control}
            name="nmrExtensionsAllowed"
            render={({ field }) => (
              <FormItem className="space-y-3">
                <FormLabel>Automatic extensions</FormLabel>
                <RadioCardGroup
                  options={NMR_EXTENSION_OPTIONS.map(option => ({
                    value: option.value,
                    label: option.label,
                  }))}
                  value={field.value}
                  onChange={field.onChange}
                  disabled={isSubmitting}
                />
                <FormDescription>
                  If a player does not submit orders, an extension resets the deadline and gives them extra time to respond before they are marked as having left the game.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating..." : "Create Game"}
        </Button>
      </form>
    </Form>
  );
};

interface CreateSandboxGameFormProps {
  onSubmit: (data: SandboxGameFormValues) => Promise<void>;
  isSubmitting: boolean;
  variants: Variant[];
}

const CreateSandboxGameForm: React.FC<CreateSandboxGameFormProps> = ({
  onSubmit,
  isSubmitting,
  variants,
}) => {
  const form = useForm<SandboxGameFormValues>({
    resolver: zodResolver(sandboxGameSchema),
    defaultValues: {
      sandboxGame: {
        name: randomGameName(),
        variantId: variants[0].id,
      },
    },
  });

  const selectedVariant = variants?.find(
    v => v.id === form.watch("sandboxGame.variantId")
  ) as Variant;

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <CardDescription>
          Practice by controlling all nations. No time limits—resolve when
          ready.
        </CardDescription>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">General</h2>

          <FormField
            control={form.control}
            name="sandboxGame.name"
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
        </div>

        <hr className="border-t" />

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Variant</h2>

          <VariantSelector
            control={form.control}
            name="sandboxGame.variantId"
            disabled={isSubmitting}
            variants={variants}
            selectedVariant={selectedVariant}
          />
        </div>

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating..." : "Create Sandbox Game"}
        </Button>
      </form>
    </Form>
  );
};

const CreateGame: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { data: allVariants } = useVariantsListSuspense();
  const variants = React.useMemo(
    () => allVariants.filter(v => v.status === "published"),
    [allVariants]
  );
  const createGameMutation = useGameCreate();
  const createSandboxGameMutation = useSandboxGameCreate();
  const checkNotificationPermission = useCheckNotificationPermission();

  const [similarMatch, setSimilarMatch] = useState<GameList | null>(null);
  const [pendingFormData, setPendingFormData] =
    useState<StandardGameFormValues | null>(null);

  const getInitialGameType = (): "standard" | "sandbox" => {
    return searchParams.get("sandbox") === "true" ? "sandbox" : "standard";
  };

  const [gameType, setGameType] = useState<"standard" | "sandbox">(
    getInitialGameType()
  );

  useEffect(() => {
    const newType = getInitialGameType();
    setGameType(newType);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const handleGameTypeChange = (value: "standard" | "sandbox") => {
    setGameType(value);

    const newSearchParams = new URLSearchParams(searchParams);
    if (value === "sandbox") {
      newSearchParams.set("sandbox", "true");
    } else {
      newSearchParams.delete("sandbox");
    }
    navigate(`?${newSearchParams.toString()}`, { replace: true });
  };

  const submitCreateGame = async (data: StandardGameFormValues) => {
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
          ...modeToBackendFields(data.mode),
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
        },
      });
      toast.success("Game created successfully");
      checkNotificationPermission();
      navigate(`/game-info/${game.id}`);
    } catch {
      toast.error("Failed to create game");
    }
  };

  const handleStandardGameSubmit = async (data: StandardGameFormValues) => {
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

  const handleSandboxGameSubmit = async (data: SandboxGameFormValues) => {
    try {
      const game = await createSandboxGameMutation.mutateAsync({
        data: data.sandboxGame,
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
      <div className="space-y-2">
        <h2 className="text-lg font-semibold">Type</h2>
        <RadioCardGroup
          options={[
            {
              value: "standard" as const,
              label: "vs Humans",
            icon: <Users className="size-6" />,
          },
          {
            value: "sandbox" as const,
            label: "Sandbox",
            icon: <Monitor className="size-6" />,
          },
        ]}
        value={gameType}
          onChange={handleGameTypeChange}
          size="large"
        />
      </div>

      <ScreenCard>
        <ScreenCardContent>
          {gameType === "standard" ? (
            <CreateStandardGameForm
              onSubmit={handleStandardGameSubmit}
              isSubmitting={createGameMutation.isPending}
              variants={variants}
            />
          ) : (
            <CreateSandboxGameForm
              onSubmit={handleSandboxGameSubmit}
              isSubmitting={createSandboxGameMutation.isPending}
              variants={variants}
            />
          )}
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
            <AlertDialogTitle>A similar game is already forming</AlertDialogTitle>
            <AlertDialogDescription>
              Join it instead to start playing sooner.
            </AlertDialogDescription>
          </AlertDialogHeader>
          {similarMatch && (
            <div className="space-y-1 text-sm">
              <p className="font-semibold">{similarMatch.name}</p>
              <p className="text-muted-foreground">
                {similarMatch.members.length}
                {matchedVariant ? ` / ${matchedVariant.nations.length}` : ""} players
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
export type { CreateStandardGameFormProps, CreateSandboxGameFormProps };
