import React, { Suspense, useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useForm, Control } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Users, Calendar, User, ChevronDown } from "lucide-react";
import { toast } from "sonner";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

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
  useVariantsListSuspense,
  useGameCreate,
  useSandboxGameCreate,
  Variant,
  MovementPhaseDurationEnum,
  NationAssignmentEnum,
} from "@/api/generated/endpoints";

const DURATION_OPTIONS = [
  { value: "1 hour", label: "1 hour" },
  { value: "12 hours", label: "12 hours" },
  { value: "24 hours", label: "24 hours" },
  { value: "48 hours", label: "48 hours" },
  { value: "3 days", label: "3 days" },
  { value: "4 days", label: "4 days" },
  { value: "1 week", label: "1 week" },
  { value: "2 weeks", label: "2 weeks" },
] as const;

const DURATION_ENUM_VALUES = [
  "1 hour",
  "12 hours",
  "24 hours",
  "48 hours",
  "3 days",
  "4 days",
  "1 week",
  "2 weeks",
] as const;

const standardGameSchema = z.object({
  name: z
    .string()
    .min(1, "Game name is required")
    .max(100, "Game name must be less than 100 characters"),
  variantId: z.string().min(1, "Please select a variant"),
  nationAssignment: z.enum(["random", "ordered"] as const),
  movementPhaseDuration: z.enum(DURATION_ENUM_VALUES).optional(),
  retreatPhaseDuration: z.enum(DURATION_ENUM_VALUES).optional().nullable(),
  private: z.boolean(),
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
      nationAssignment: "random" as NationAssignmentEnum,
      movementPhaseDuration: "24 hours" as MovementPhaseDurationEnum,
      retreatPhaseDuration: null,
      private: false,
    },
  });

  const selectedVariant = variants?.find(v => v.id === form.watch("variantId"));

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
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

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Deadlines</h2>

          <FormField
            control={form.control}
            name="movementPhaseDuration"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Movement Phase Deadline</FormLabel>
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
                    {DURATION_OPTIONS.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormDescription>
                  Deadline for movement phases
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <Collapsible>
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                type="button"
                className="gap-2 p-0 h-auto font-normal text-muted-foreground hover:text-foreground"
              >
                <ChevronDown className="h-4 w-4" />
                Advanced duration options
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-4">
              <FormField
                control={form.control}
                name="retreatPhaseDuration"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Retreat/Adjustment Phase Deadline</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value ?? undefined}
                      disabled={isSubmitting}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Same as movement phase" />
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
                    <FormDescription>
                      If not set, uses the same deadline as movement phases
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CollapsibleContent>
          </Collapsible>

          <div className="text-sm text-muted-foreground pt-2">
            <DeadlineSummary
              movementPhaseDuration={form.watch("movementPhaseDuration") ?? null}
              retreatPhaseDuration={form.watch("retreatPhaseDuration") ?? null}
            />
          </div>
        </div>

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
  const { data: variants } = useVariantsListSuspense();
  const createGameMutation = useGameCreate();
  const createSandboxGameMutation = useSandboxGameCreate();

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

  const handleStandardGameSubmit = async (data: StandardGameFormValues) => {
    try {
      const game = await createGameMutation.mutateAsync({ data });
      toast.success("Game created successfully");
      navigate(`/game-info/${game.id}`);
    } catch {
      toast.error("Failed to create game");
    }
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

export { CreateGameSuspense as CreateGame };
export type { CreateStandardGameFormProps, CreateSandboxGameFormProps };
