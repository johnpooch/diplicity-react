import { BookOpen, Calendar, Trophy, User } from "lucide-react";

import type { Variant } from "@/api/generated/endpoints";
import type { SettingsRow } from "@/components/SettingsTable";

const formatList = (items: string[]) =>
  items.length > 1
    ? `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`
    : items.join("");

function buildVictoryRule(variant: Variant): string | null {
  const defaultTarget = variant.victoryConditions.soloVictorySupplyCenters;
  const overrides = variant.nations.filter(
    ({ nonPlayable, soloVictorySupplyCenters }) =>
      !nonPlayable &&
      soloVictorySupplyCenters !== null &&
      soloVictorySupplyCenters !== defaultTarget
  );
  const nationTargets = formatList(
    overrides.map(
      ({ name, soloVictorySupplyCenters }) =>
        `${name} (${soloVictorySupplyCenters})`
    )
  );

  if (defaultTarget === null) {
    return overrides.length === 0
      ? null
      : `Solo victory: ${nationTargets} supply centres. Other nations cannot win solo.`;
  }

  return overrides.length === 0
    ? `Solo victory: ${defaultTarget} supply centres.`
    : `Solo victory: ${defaultTarget} supply centres, except ${nationTargets}.`;
}

function buildVariantInfoRows(variant: Variant): SettingsRow[] {
  const rules = [buildVictoryRule(variant), variant.rules]
    .filter(Boolean)
    .join("\n\n");

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
    ...(rules
      ? [{ key: "rules", icon: Trophy, label: "Rules", text: rules }]
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
