import React from "react";
import { type LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { InfoButton } from "@/components/InfoButton";

interface SettingsRow {
  key: string;
  icon?: LucideIcon;
  label: string;
  value?: React.ReactNode;
  info?: string;
  text?: string;
}

const SettingsTable: React.FC<{ rows: SettingsRow[] }> = ({ rows }) => {
  if (rows.length === 0) {
    return null;
  }

  return (
    <Card className="overflow-hidden py-0">
      <CardContent className="flex flex-col divide-y p-0">
        {rows.map(row => (
          <div key={row.key} className="px-6 py-3">
            <div className="flex items-center justify-between gap-4">
              <span className="flex min-w-0 items-center gap-3 text-sm">
                {row.icon && (
                  <row.icon className="size-4 shrink-0 text-muted-foreground" />
                )}
                <span className="flex min-w-0 items-center gap-1">
                  {row.label}
                  {row.info && <InfoButton label={row.label} text={row.info} />}
                </span>
              </span>
              {row.value !== undefined && (
                <span className="truncate text-sm text-muted-foreground">
                  {row.value}
                </span>
              )}
            </div>
            {row.text && (
              <p className="mt-1 whitespace-pre-line pl-7 text-sm text-muted-foreground">
                {row.text}
              </p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export { SettingsTable };
export type { SettingsRow };
