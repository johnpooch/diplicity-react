import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useForm, Control } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Users, Calendar, User } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
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

import {
  service,
  VariantRead,
  MovementPhaseDurationEnum,
  NationAssignmentEnum,
} from "@/store";
import { randomGameName } from "@/util";
import { InteractiveMap } from "@/components/InteractiveMap/InteractiveMap";
import { HomeLayout } from "./Layout";

type VariantForSelector = Pick<
  VariantRead,
  "id" | "name" | "nations" | "author" | "templatePhase"
>;

const standardGameSchema = z.object({
  name: z
    .string()
    .min(1, "Game name is required")
    .max(100, "Game name must be less than 100 characters"),
  variantId: z.string().min(1, "Please select a variant"),
  nationAssignment: z.enum(["random", "ordered"] as const),
  movementPhaseDuration: z
    .enum(["24 hours", "48 hours", "1 week"] as const)
    .optional(),
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
  variants: VariantForSelector[] | undefined;
  isLoadingVariants: boolean;
  selectedVariant: VariantForSelector | undefined;
}

const VariantSelector: React.FC<VariantSelectorProps> = ({
  control,
  name,
  disabled,
  variants,
  isLoadingVariants,
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
              disabled={disabled || isLoadingVariants}
            >
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select a variant" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {variants?.map((variant) => (
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

      {isLoadingVariants ? (
        <Skeleton className="h-96 w-full" />
      ) : selectedVariant?.templatePhase ? (
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
            value: isLoadingVariants ? (
              <Skeleton className="h-4 w-20" />
            ) : (
              selectedVariant?.nations.length.toString()
            ),
            icon: <Users className="size-4" />,
          },
          {
            label: "Start year",
            value: isLoadingVariants ? (
              <Skeleton className="h-4 w-20" />
            ) : (
              selectedVariant?.templatePhase.year.toString()
            ),
            icon: <Calendar className="size-4" />,
          },
          {
            label: "Original author",
            value: isLoadingVariants ? (
              <Skeleton className="h-4 w-20" />
            ) : (
              selectedVariant?.author
            ),
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
  variants: VariantForSelector[] | undefined;
  isLoadingVariants: boolean;
}

const CreateStandardGameForm: React.FC<CreateStandardGameFormProps> = ({
  onSubmit,
  isSubmitting,
  variants,
  isLoadingVariants,
}) => {
  const form = useForm<StandardGameFormValues>({
    resolver: zodResolver(standardGameSchema),
    defaultValues: {
      name: randomGameName(),
      variantId: "classical",
      nationAssignment: "random" as NationAssignmentEnum,
      movementPhaseDuration: "24 hours" as MovementPhaseDurationEnum,
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
                <FormLabel>Phase Deadline</FormLabel>
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
                    <SelectItem value="24 hours">24 hours</SelectItem>
                    <SelectItem value="48 hours">48 hours</SelectItem>
                    <SelectItem value="1 week">1 week</SelectItem>
                  </SelectContent>
                </Select>
                <FormDescription>
                  After the deadline, the phase will be automatically resolved
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Variant</h2>

          <VariantSelector
            control={form.control}
            name="variantId"
            disabled={isSubmitting}
            variants={variants}
            isLoadingVariants={isLoadingVariants}
            selectedVariant={selectedVariant}
          />
        </div>

        <Button
          type="submit"
          className="w-full"
          disabled={isSubmitting || isLoadingVariants}
        >
          {isSubmitting ? "Creating..." : "Create Game"}
        </Button>
      </form>
    </Form>
  );
};

interface CreateSandboxGameFormProps {
  onSubmit: (data: SandboxGameFormValues) => Promise<void>;
  isSubmitting: boolean;
  variants: VariantForSelector[] | undefined;
  isLoadingVariants: boolean;
}

const CreateSandboxGameForm: React.FC<CreateSandboxGameFormProps> = ({
  onSubmit,
  isSubmitting,
  variants,
  isLoadingVariants,
}) => {
  const form = useForm<SandboxGameFormValues>({
    resolver: zodResolver(sandboxGameSchema),
    defaultValues: {
      sandboxGame: {
        name: randomGameName(),
        variantId: "classical",
      },
    },
  });

  const selectedVariant = variants?.find(
    v => v.id === form.watch("sandboxGame.variantId")
  );

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
              isLoadingVariants={isLoadingVariants}
              selectedVariant={selectedVariant}
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={isSubmitting || isLoadingVariants}
          >
            {isSubmitting ? "Creating..." : "Create Sandbox Game"}
          </Button>
        </form>
      </Form>
  );
};

interface CreateGameProps {
  currentTab: "standard" | "sandbox";
  onTabChange: (value: string) => void;
  onStandardGameSubmit: (data: StandardGameFormValues) => Promise<void>;
  onSandboxGameSubmit: (data: SandboxGameFormValues) => Promise<void>;
  isStandardGameSubmitting: boolean;
  isSandboxGameSubmitting: boolean;
  variants: VariantForSelector[] | undefined;
  isLoadingVariants: boolean;
}

const CreateGame: React.FC<CreateGameProps> = ({
  currentTab,
  onTabChange,
  onStandardGameSubmit,
  onSandboxGameSubmit,
  isStandardGameSubmitting,
  isSandboxGameSubmitting,
  variants,
  isLoadingVariants,
}) => {
  return (
    <div className="w-full space-y-4">
      <h1 className="text-2xl font-bold">Create Game</h1>

      <Tabs value={currentTab} onValueChange={onTabChange}>
        <TabsList className="w-full">
          <TabsTrigger value="standard" className="flex-1">
            Standard
          </TabsTrigger>
          <TabsTrigger value="sandbox" className="flex-1">
            Sandbox
          </TabsTrigger>
        </TabsList>

        <TabsContent value="standard">
          <Card>
            <CardContent className="p-6">
              <CreateStandardGameForm
                onSubmit={onStandardGameSubmit}
                isSubmitting={isStandardGameSubmitting}
                variants={variants}
                isLoadingVariants={isLoadingVariants}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sandbox">
          <Card>
            <CardContent className="p-6">
              <CreateSandboxGameForm
                onSubmit={onSandboxGameSubmit}
                isSubmitting={isSandboxGameSubmitting}
                variants={variants}
                isLoadingVariants={isLoadingVariants}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const CreateGameContainer: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

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

  const variantsQuery = service.endpoints.variantsList.useQuery(undefined);
  const [createGame, createGameResult] =
    service.endpoints.gameCreate.useMutation();
  const [createSandboxGame, createSandboxGameResult] =
    service.endpoints.sandboxGameCreate.useMutation();

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
      await createGame({ game: data }).unwrap();
      navigate("/");
    } catch (error) {
      console.error("Failed to create game:", error);
    }
  };

  const handleSandboxGameSubmit = async (data: SandboxGameFormValues) => {
    try {
      await createSandboxGame(data).unwrap();
      navigate("/");
    } catch (error) {
      console.error("Failed to create sandbox game:", error);
    }
  };

  return (
    <HomeLayout
      content={
        <CreateGame
          currentTab={currentTab}
          onTabChange={handleTabChange}
          onStandardGameSubmit={handleStandardGameSubmit}
          onSandboxGameSubmit={handleSandboxGameSubmit}
          isStandardGameSubmitting={createGameResult.isLoading}
          isSandboxGameSubmitting={createSandboxGameResult.isLoading}
          variants={variantsQuery.data}
          isLoadingVariants={variantsQuery.isLoading}
        />
      }
    />
  );
};

export { CreateGame, CreateGameContainer };
export type {
  CreateGameProps,
  CreateStandardGameFormProps,
  CreateSandboxGameFormProps,
  VariantForSelector,
};
