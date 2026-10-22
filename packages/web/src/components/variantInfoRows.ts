import { BookOpen, Calendar, Target, Trophy, User } from "lucide-react";

import type { Variant } from "@/api/generated/endpoints";
import type { SettingsRow } from "@/components/SettingsTable";

const formatSupplyCenters = (count: number) =>
  `${count} supply ${count === 1 ? "centre" : "centres"}`;

function buildVictoryRow(variant: Variant): SettingsRow | null {
  const defaultTarget = variant.victoryConditions.soloVictorySupplyCenters;
  const overrides = variant.nations.flatMap(
    ({ name, nonPlayable, soloVictorySupplyCenters }) =>
      nonPlayable ||
      soloVictorySupplyCenters === null ||
      soloVictorySupplyCenters === defaultTarget
        ? []
        : [`${name}: ${formatSupplyCenters(soloVictorySupplyCenters)}`]
  );

  if (defaultTarget === null && overrides.length === 0) return null;

  return {
    key: "victory",
    icon: Target,
    label: "Solo victory",
    value:
      defaultTarget === null
        ? "Varies by nation"
        : formatSupplyCenters(defaultTarget),
    ...(overrides.length > 0 && {
      text: [
        ...overrides,
        defaultTarget === null
          ? "Other nations cannot win solo"
          : `Every other nation: ${formatSupplyCenters(defaultTarget)}`,
      ].join("\n"),
    }),
  };
}

function buildVariantInfoRows(variant: Variant): SettingsRow[] {
  const victoryRow = buildVictoryRow(variant);

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
    ...(victoryRow ? [victoryRow] : []),
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
