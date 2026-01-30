import { useEffect, useId } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { NationColorPicker } from "@/components/common/NationColorPicker";
import { useVariant } from "@/hooks/useVariant";

const DEFAULT_COLORS = [
  "#2196F3",
  "#F44336",
  "#4CAF50",
  "#FFC107",
  "#9C27B0",
  "#00BCD4",
  "#607D8B",
  "#FF5722",
];

const nationSchema = z.object({
  id: z.string(),
  name: z.string().min(1, "Nation name is required"),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, "Invalid color format"),
});

const phaseSetupSchema = z.object({
  name: z.string().min(1, "Variant name is required"),
  description: z.string(),
  author: z.string(),
  soloVictorySCCount: z
    .number()
    .min(1, "Must be at least 1")
    .int("Must be a whole number"),
  nations: z
    .array(nationSchema)
    .min(2, "At least 2 nations are required")
    .refine(
      (nations) =>
        new Set(nations.map((n) => n.name.toLowerCase())).size ===
        nations.length,
      "Nation names must be unique"
    ),
});

type PhaseSetupFormValues = z.infer<typeof phaseSetupSchema>;

function generateNationId(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]/g, "") || `nation-${Date.now()}`;
}

export function PhaseSetup() {
  const formId = useId();
  const { variant, updateMetadata, setNations } = useVariant();

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<PhaseSetupFormValues>({
    resolver: zodResolver(phaseSetupSchema),
    defaultValues: {
      name: variant?.name || "",
      description: variant?.description || "",
      author: variant?.author || "",
      soloVictorySCCount: variant?.soloVictorySCCount || 18,
      nations: variant?.nations?.length
        ? variant.nations
        : [
            { id: "nation-1", name: "", color: DEFAULT_COLORS[0] },
            { id: "nation-2", name: "", color: DEFAULT_COLORS[1] },
          ],
    },
    mode: "onChange",
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "nations",
  });

  const watchedNations = watch("nations");
  const watchedName = watch("name");
  const watchedDescription = watch("description");
  const watchedAuthor = watch("author");
  const watchedSoloVictorySCCount = watch("soloVictorySCCount");

  useEffect(() => {
    updateMetadata({
      name: watchedName,
      description: watchedDescription,
      author: watchedAuthor,
      soloVictorySCCount: Number(watchedSoloVictorySCCount) || 0,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally only sync when values change
  }, [
    watchedName,
    watchedDescription,
    watchedAuthor,
    watchedSoloVictorySCCount,
  ]);

  const nationsJson = JSON.stringify(watchedNations);
  useEffect(() => {
    const nations = JSON.parse(nationsJson) as typeof watchedNations;
    const validNations = nations.filter(
      (n) => n.name.trim() && /^#[0-9A-Fa-f]{6}$/.test(n.color)
    );
    if (validNations.length > 0) {
      setNations(
        validNations.map((n) => ({
          ...n,
          id: generateNationId(n.name) || n.id,
        }))
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally only sync when nations change
  }, [nationsJson]);

  const handleAddNation = () => {
    const nextColorIndex = fields.length % DEFAULT_COLORS.length;
    append({
      id: `nation-${Date.now()}`,
      name: "",
      color: DEFAULT_COLORS[nextColorIndex],
    });
  };

  const handleRemoveNation = (index: number) => {
    if (fields.length > 2) {
      remove(index);
    }
  };

  const onSubmit = (data: PhaseSetupFormValues) => {
    console.log("Form submitted:", data);
  };

  return (
    <form id={formId} onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Variant Information</CardTitle>
          <CardDescription>
            Basic information about your Diplomacy variant.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor={`${formId}-name`}>Variant Name *</Label>
            <Input
              id={`${formId}-name`}
              {...register("name")}
              placeholder="e.g., Classical Europe"
              aria-invalid={!!errors.name}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor={`${formId}-description`}>Description</Label>
            <Textarea
              id={`${formId}-description`}
              {...register("description")}
              placeholder="A brief description of your variant..."
              rows={3}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor={`${formId}-author`}>Author</Label>
              <Input
                id={`${formId}-author`}
                {...register("author")}
                placeholder="Your name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor={`${formId}-sc-count`}>
                Solo Victory SC Count *
              </Label>
              <Input
                id={`${formId}-sc-count`}
                type="number"
                min={1}
                {...register("soloVictorySCCount", { valueAsNumber: true })}
                aria-invalid={!!errors.soloVictorySCCount}
              />
              {errors.soloVictorySCCount && (
                <p className="text-sm text-destructive">
                  {errors.soloVictorySCCount.message}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Nations</CardTitle>
          <CardDescription>
            Define the nations that will play in this variant. You need at least
            2 nations with unique names.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {errors.nations?.root && (
            <p className="text-sm text-destructive">
              {errors.nations.root.message}
            </p>
          )}

          <div className="space-y-3">
            {fields.map((field, index) => (
              <div
                key={field.id}
                className="flex items-start gap-3 rounded-lg border bg-muted/30 p-3"
              >
                <NationColorPicker
                  value={watchedNations[index]?.color || DEFAULT_COLORS[0]}
                  onChange={(color) => setValue(`nations.${index}.color`, color)}
                />

                <div className="flex-1 space-y-1">
                  <Input
                    {...register(`nations.${index}.name`)}
                    placeholder="Nation name"
                    aria-invalid={!!errors.nations?.[index]?.name}
                  />
                  {errors.nations?.[index]?.name && (
                    <p className="text-sm text-destructive">
                      {errors.nations[index]?.name?.message}
                    </p>
                  )}
                </div>

                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => handleRemoveNation(index)}
                  disabled={fields.length <= 2}
                  aria-label="Remove nation"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={handleAddNation}
            className="w-full"
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Nation
          </Button>
        </CardContent>
      </Card>
    </form>
  );
}
