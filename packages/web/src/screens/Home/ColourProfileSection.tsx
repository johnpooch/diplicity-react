import React, { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  getUserRetrieveQueryKey,
  useUserRetrieveSuspense,
  useUserUpdatePartialUpdate,
  type UserProfile,
} from "@/api/generated/endpoints";
import { useQueryClient } from "@tanstack/react-query";

const COLOUR_PALETTE = [
  "#FFCDD2", "#F8BBD9", "#E1BEE7", "#BBDEFB", "#B2DFDB", "#DCEDC8", "#FFF9C4", "#F5F5F5",
  "#EF9A9A", "#F48FB1", "#CE93D8", "#90CAF9", "#80CBC4", "#AED581", "#FFF176", "#BDBDBD",
  "#EF5350", "#EC407A", "#AB47BC", "#42A5F5", "#26A69A", "#66BB6A", "#FFEE58", "#8D6E63",
  "#E53935", "#E91E63", "#9C27B0", "#2196F3", "#009688", "#4CAF50", "#FDD835", "#795548",
  "#C62828", "#AD1457", "#6A1B9A", "#1565C0", "#00695C", "#2E7D32", "#F57F17", "#4E342E",
  "#B71C1C", "#880E4F", "#4A148C", "#0D47A1", "#004D40", "#1B5E20", "#E65100", "#212121",
];

const HEX_PATTERN = /^#[0-9A-Fa-f]{6}$/;

const ColourProfileSection: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: userProfile } = useUserRetrieveSuspense();
  const updateMutation = useUserUpdatePartialUpdate();

  const savedColours = userProfile.customColourProfile;
  const savedColoursRef = useRef(savedColours);
  savedColoursRef.current = savedColours;

  const [localColours, setLocalColours] = useState<string[]>(savedColours);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      abortControllerRef.current?.abort();
    };
  }, []);

  const defaultColourProfile = userProfile.defaultColourProfile ?? [];
  const isDefaultColours =
    defaultColourProfile.length === localColours.length &&
    defaultColourProfile.every((c, i) => c === localColours[i]);

  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingColour, setEditingColour] = useState("#000000");
  const [hexInput, setHexInput] = useState("#000000");
  const isValidEditHex = HEX_PATTERN.test(hexInput);

  const handleSwatchClick = (index: number) => {
    setEditingIndex(index);
    setEditingColour(localColours[index]);
    setHexInput(localColours[index]);
  };

  const handlePickPreset = (colour: string) => {
    setEditingColour(colour);
    setHexInput(colour);
  };

  const handleHexInput = (value: string) => {
    setHexInput(value);
    if (HEX_PATTERN.test(value)) setEditingColour(value);
  };

  const handleApplyColour = () => {
    if (editingIndex !== null) handleColourChange(editingIndex, editingColour);
    setEditingIndex(null);
  };

  const handleToggle = async (checked: boolean) => {
    queryClient.setQueryData<UserProfile>(getUserRetrieveQueryKey(), prev => ({
      ...prev!,
      colourProfileEnabled: checked,
    }));
    try {
      const result = await updateMutation.mutateAsync({
        data: { colourProfileEnabled: checked },
      });
      queryClient.setQueryData(getUserRetrieveQueryKey(), result);
    } catch {
      queryClient.setQueryData<UserProfile>(getUserRetrieveQueryKey(), prev => ({
        ...prev!,
        colourProfileEnabled: !checked,
      }));
      toast.error("Failed to update colour setting");
    }
  };

  const handleColourChange = (index: number, colour: string) => {
    const next = localColours.map((c, i) => (i === index ? colour : c));
    setLocalColours(next);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;
      updateMutation
        .mutateAsync({ data: { customColourProfile: next } })
        .then(result => {
          if (!controller.signal.aborted)
            queryClient.setQueryData(getUserRetrieveQueryKey(), result);
        })
        .catch(() => {
          if (!controller.signal.aborted) {
            setLocalColours(savedColoursRef.current);
            toast.error("Failed to save colour profile");
          }
        });
    }, 600);
  };

  const handleResetColours = () => {
    const defaults = defaultColourProfile;
    setLocalColours(defaults);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;
    updateMutation
      .mutateAsync({ data: { customColourProfile: defaults } })
      .then(result => {
        if (!controller.signal.aborted)
          queryClient.setQueryData(getUserRetrieveQueryKey(), result);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setLocalColours(savedColoursRef.current);
          toast.error("Failed to reset colour profile");
        }
      });
  };

  return (
    <>
      <div
        className={cn(
          "rounded-lg border transition-all duration-300",
          userProfile.colourProfileEnabled
            ? "border-border shadow-md p-4"
            : "border-transparent shadow-none p-0",
        )}
      >
        <div className="flex items-center space-x-2">
          <Switch
            id="colour-profile"
            checked={userProfile.colourProfileEnabled}
            disabled={updateMutation.isPending}
            onCheckedChange={handleToggle}
          />
          <div className="flex flex-col">
            <Label htmlFor="colour-profile">Custom nation colours</Label>
            <span className="text-xs text-muted-foreground">Colourblind mode</span>
          </div>
        </div>
        <div
          className={cn(
            "grid transition-all duration-300",
            userProfile.colourProfileEnabled ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
          )}
        >
          <div className="overflow-hidden">
            <div className="mt-3 space-y-3">
              <p className="text-sm text-muted-foreground">
                Nation colours will be replaced with these colours, in order,
                across all variants.
              </p>
              <div className="grid grid-cols-6 gap-2">
                {localColours.map((colour, i) => (
                  <div key={i} className="flex items-center gap-1">
                    <span className="text-xs text-muted-foreground w-4 text-right">
                      {i + 1}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleSwatchClick(i)}
                      className="size-8 rounded-full border border-border/40 transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1"
                      style={{ backgroundColor: colour }}
                      aria-label={`Colour ${i + 1}: ${colour}`}
                    />
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleResetColours}
                  disabled={isDefaultColours || updateMutation.isPending}
                >
                  Reset to defaults
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <Sheet
        open={editingIndex !== null}
        onOpenChange={open => {
          if (!open) setEditingIndex(null);
        }}
      >
        <SheetContent side="bottom">
          <SheetHeader>
            <SheetTitle>
              {editingIndex !== null ? `Colour ${editingIndex + 1}` : ""}
            </SheetTitle>
          </SheetHeader>
          <div className="px-4 space-y-4">
            <div className="flex items-center gap-3">
              <div
                className="size-10 rounded-full border border-border/40 shrink-0"
                style={{ backgroundColor: editingColour }}
              />
              <Input
                value={hexInput}
                onChange={e => handleHexInput(e.target.value)}
                placeholder="#000000"
                className={cn(
                  "font-mono",
                  !isValidEditHex && hexInput !== "" && "border-destructive",
                )}
              />
            </div>
            <div className="grid grid-cols-8 gap-2">
              {COLOUR_PALETTE.map(colour => (
                <button
                  key={colour}
                  type="button"
                  onClick={() => handlePickPreset(colour)}
                  className={cn(
                    "size-9 rounded-full border-2 transition-transform hover:scale-110 focus:outline-none",
                    colour === editingColour ? "border-foreground" : "border-transparent",
                  )}
                  style={{ backgroundColor: colour }}
                  aria-label={colour}
                />
              ))}
            </div>
          </div>
          <SheetFooter>
            <Button variant="outline" onClick={() => setEditingIndex(null)}>
              Cancel
            </Button>
            <Button onClick={handleApplyColour} disabled={!isValidEditHex}>
              Apply
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </>
  );
};

export { ColourProfileSection };
