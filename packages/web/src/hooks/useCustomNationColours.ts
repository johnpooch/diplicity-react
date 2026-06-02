import { useCallback } from "react";
import { useUserRetrieveSuspense, type Nation } from "@/api/generated/endpoints";

export function useCustomNationColours(): (nations: Nation[]) => Nation[] {
  const { data: userProfile } = useUserRetrieveSuspense();

  return useCallback(
    (nations: Nation[]): Nation[] => {
      const profile = userProfile.customColourProfile;
      if (!userProfile.colourProfileEnabled || !Array.isArray(profile) || profile.length === 0) {
        return nations;
      }
      const sorted = [...nations].sort((a, b) => a.name.localeCompare(b.name));
      const colourMap = new Map(sorted.map((n, i) => [n.name, profile[i] ?? n.color]));
      return nations.map(n => ({ ...n, color: colourMap.get(n.name) ?? n.color }));
    },
    [userProfile.colourProfileEnabled, userProfile.customColourProfile],
  );
}
