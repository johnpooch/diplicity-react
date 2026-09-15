import { BookOpen, Calendar, Trophy, User } from "lucide-react";

import type { Variant } from "@/api/generated/endpoints";
import type { SettingsRow } from "@/components/SettingsTable";

function buildVariantInfoRows(variant: Variant): SettingsRow[] {
  return [
    ...(variant.description
      ? [
          {
            key: "description",
            icon: BookOpen,
            label: "Description",
            text: variant.description,
          },
        ]
      : []),
    ...(variant.rules
      ? [{ key: "rules", icon: Trophy, label: "Rules", text: variant.rules }]
      : []),
    {
      key: "start-year",
      icon: Calendar,
      label: "Start year",
      value: variant.templatePhase.year.toString(),
    },
    ...(variant.author
      ? [
          {
            key: "author",
            icon: User,
            label: "Original author",
            value: variant.author,
          },
        ]
      : []),
  ];
}

export { buildVariantInfoRows };
