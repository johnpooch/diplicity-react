import React, { Suspense, useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useForm, Control } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Users, Calendar, User, Clock } from "lucide-react";
import { toast } from "sonner";

import { Alert, AlertDescription } from "@/components/ui/alert";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CardDescription } from "@/components/ui/card";
import { ScreenCard, ScreenCardContent } from "@/components/ui/screen-card";
import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";

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
import { InteractiveMap } from "@/components/InteractiveMap/InteractiveMap";
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

interface MetadataRow {
  label: string;
  value: string | React.ReactNode;
  icon?: React.ReactNode;
}

interface GameMetadataTableProps {
  rows: MetadataRow[];
}

const GameMetadataTable: React.FC<GameMetadataTableProps> = ({ rows }) => {
  return (
    <div className="divide-y border rounded-lg">
      {rows.map((row, index) => (
        <div key={index} className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            {row.icon}
            <span className="text-sm">{row.label}</span>
          </div>
          <span className="text-sm text-muted-foreground">{row.value}</span>
        </div>
      ))}
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
                <SelectTrigger>
                  <SelectValue placeholder="Select a variant" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {variants?.map(variant => (
                  <SelectItem key={variant.id} value={variant.id}>
                    {variant.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />

      {selectedVariant?.templatePhase ? (
        <InteractiveMap
          variant={selectedVariant}
          phase={selectedVariant.templatePhase}
          interactive={false}
          selected={[]}
          orders={undefined}
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
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">General</h2>

          <FormField
            control={form.control}
            name="mode"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Mode</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  value={field.value}
                  disabled={isSubmitting}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="standard">Standard</SelectItem>
                    <SelectItem value="gunboat">Gunboat</SelectItem>
                  </SelectContent>
                </Select>
                <FormDescription>
                  {field.value === "gunboat"
                    ? "Player names are anonymized and messaging is disabled"
                    : "Standard play"}
                </FormDescription>
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
                    onCheckedChange={field.onChange}
                    disabled={isSubmitting}
                  />
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel>Private</FormLabel>
                  <FormDescription>
                    Make this game private (only accessible via direct link, not
                    shown in public listings)
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
              <FormItem>
                <Tabs
                  value={field.value}
                  onValueChange={field.onChange}
                  className="w-full"
                >
                  <TabsList className="w-full">
                    <TabsTrigger value="fixed_time" className="flex-1">
                      Fixed Time
                    </TabsTrigger>
                    <TabsTrigger value="duration" className="flex-1">
                      Duration
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="duration" className="space-y-4 pt-4">
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
                  </TabsContent>

                  <TabsContent value="fixed_time" className="space-y-4 pt-4">
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
                  </TabsContent>
                </Tabs>
              </FormItem>
            )}
          />

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
              <FormItem>
                <FormLabel>Automatic Extensions</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  value={field.value}
                  disabled={isSubmitting}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {NMR_EXTENSION_OPTIONS.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormDescription>
                  Automatic extensions when players miss the deadline
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
  const { data: variants } = useVariantsListSuspense();
  const createGameMutation = useGameCreate();
  const createSandboxGameMutation = useSandboxGameCreate();

  const [similarMatch, setSimilarMatch] = useState<GameList | null>(null);
  const [pendingFormData, setPendingFormData] =
    useState<StandardGameFormValues | null>(null);

  const getInitialTab = (): "standard" | "sandbox" => {
    return searchParams.get("sandbox") === "true" ? "sandbox" : "standard";
  };

  const [currentTab, setCurrentTab] = useState<"standard" | "sandbox">(
    getInitialTab()
  );

  useEffect(() => {
    const newTab = getInitialTab();
    setCurrentTab(newTab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const handleTabChange = (value: string) => {
    const newTab = value as "standard" | "sandbox";
    setCurrentTab(newTab);

    const newSearchParams = new URLSearchParams(searchParams);
    if (newTab === "sandbox") {
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
      <Tabs value={currentTab} onValueChange={handleTabChange}>
        <TabsList className="w-full">
          <TabsTrigger value="standard" className="flex-1">
            Standard
          </TabsTrigger>
          <TabsTrigger value="sandbox" className="flex-1">
            Sandbox
          </TabsTrigger>
        </TabsList>

        <TabsContent value="standard">
          <ScreenCard>
            <ScreenCardContent>
              <CreateStandardGameForm
                onSubmit={handleStandardGameSubmit}
                isSubmitting={createGameMutation.isPending}
                variants={variants}
              />
            </ScreenCardContent>
          </ScreenCard>
        </TabsContent>

        <TabsContent value="sandbox">
          <ScreenCard>
            <ScreenCardContent>
              <CreateSandboxGameForm
                onSubmit={handleSandboxGameSubmit}
                isSubmitting={createSandboxGameMutation.isPending}
                variants={variants}
              />
            </ScreenCardContent>
          </ScreenCard>
        </TabsContent>
      </Tabs>

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
      <ScreenHeader title="Create Game" showUserAvatar />
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
