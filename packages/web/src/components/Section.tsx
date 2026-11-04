import React from "react";

import { Card, CardContent } from "@/components/ui/card";
import { InfoButton } from "@/components/InfoButton";

interface SectionProps {
  title: string;
  info?: string;
  children: React.ReactNode;
}

const Section: React.FC<SectionProps> = ({ title, info, children }) => (
  <section className="flex flex-col gap-2">
    <h2 className="flex items-center gap-1 text-sm font-medium text-muted-foreground">
      {title}
      {info && <InfoButton label={title} text={info} />}
    </h2>
    <Card className="overflow-hidden py-0">
      <CardContent className="p-0">{children}</CardContent>
    </Card>
  </section>
);

interface StatRowProps {
  label: string;
  value: React.ReactNode;
}

const StatRow: React.FC<StatRowProps> = ({ label, value }) => (
  <div className="flex items-center justify-between gap-4 px-6 py-3 text-sm">
    <span>{label}</span>
    <span className="tabular-nums text-muted-foreground">{value}</span>
  </div>
);

export { Section, StatRow };
