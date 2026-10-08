import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";

export type Label = "reasonable" | "unreasonable";

export type Phase = { season: string; year: number; type: string };

export type Unit = {
  type: "Army" | "Fleet";
  nation: string;
  province: string;
  dislodged: boolean;
};

export type BoardState = {
  id: string;
  nation: string;
  phase: Phase;
  units: Unit[];
  supply_centers: { nation: string; province: string }[];
};

export type OrderDetail = {
  source: string;
  order_type: string;
  target: string | null;
  aux: string | null;
  unit_type: string | null;
  named_coast: string | null;
  source_name: string;
  description: string;
};

export type FixtureSummary = {
  id: string;
  nation: string;
  phase: Phase;
  labels: Partial<Record<Label, number>>;
};

export type OrderSet = {
  orders: string[];
  name: string;
  label: Label;
  reason: string;
};

export type FixtureDetail = BoardState & {
  notes: string;
  max_orders: number | null;
  options: string[];
  orders: Record<string, OrderDetail>;
  order_sets: OrderSet[];
};

export type RunHeader = { name: string; id: string; model: string; created: string };

export type RunCounts = {
  answers: number;
  order_sets: number;
  reasonable: number;
  unreasonable: number;
  new: number;
  matched: number;
  unanswered: number;
  score: number | null;
};

export type RunDetail = RunHeader &
  RunCounts & {
    fixtures: (RunCounts & { id: string; nation: string; phase: Phase })[];
  };

export type Reasoning = { epoch: number; reasoning: string };

export type QueueItem = {
  fixture: BoardState;
  orders: string[];
  name: string;
  details: Record<string, OrderDetail>;
  reasonings: Reasoning[];
};

export type RunOrderSet = {
  orders: string[];
  name: string;
  details: Record<string, OrderDetail>;
  label: Label | null;
  reason: string;
  epochs: number[];
  reasonings: Reasoning[];
};

export type UnusableAnswer = { epoch: number; problem: string; completion: string };

export type RunFixture = {
  fixture: BoardState;
  summary: RunCounts;
  order_sets: RunOrderSet[];
  unusable: UnusableAnswer[];
};

export type RunQueue = { matched: number; items: QueueItem[] };

export type FixturePrompts = { fixture: string; system?: string; user?: string };

export type LabelOrderSet = {
  fixtureId: string;
  orders: string[];
  label: Label;
  reason: string;
};

const request = async <T>(url: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(url, init);
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error ?? `${response.status} ${response.statusText}`);
  }
  return body as T;
};

const runUrl = (name: string) => `/api/runs/${encodeURIComponent(name)}/`;

export const useFixtures = () =>
  useSuspenseQuery({
    queryKey: ["fixtures"],
    queryFn: () => request<{ fixtures: FixtureSummary[] }>("/api/fixtures/").then(body => body.fixtures),
  });

export const useFixture = (fixtureId: string) =>
  useSuspenseQuery({
    queryKey: ["fixtures", fixtureId],
    queryFn: () => request<FixtureDetail>(`/api/fixtures/${fixtureId}/`),
  });

export const useRuns = () =>
  useSuspenseQuery({
    queryKey: ["runs"],
    queryFn: () => request<{ runs: RunHeader[] }>("/api/runs/").then(body => body.runs),
  });

export const useRun = (name: string) =>
  useSuspenseQuery({
    queryKey: ["runs", name],
    queryFn: () => request<RunDetail>(runUrl(name)),
  });

export const useRunQueue = (name: string) =>
  useSuspenseQuery({
    queryKey: ["runs", name, "queue"],
    queryFn: () => request<RunQueue>(`${runUrl(name)}queue/`),
  });

export const useRunFixture = (name: string, fixtureId: string) =>
  useSuspenseQuery({
    queryKey: ["runs", name, "fixtures", fixtureId],
    queryFn: () => request<RunFixture>(`${runUrl(name)}fixtures/${fixtureId}/`),
  });

export const useRunPrompts = (name: string) =>
  useSuspenseQuery({
    queryKey: ["prompts", name],
    queryFn: () =>
      request<{ prompts: FixturePrompts[] }>(`${runUrl(name)}prompts/`).then(body => body.prompts),
  });

export const useLabelOrderSet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ fixtureId, ...body }: LabelOrderSet) =>
      request<{ orders: string[] }>(`/api/fixtures/${fixtureId}/order-set-labels/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: ["fixtures"], refetchType: "all" }),
        queryClient.invalidateQueries({ queryKey: ["runs"], refetchType: "all" }),
      ]),
  });
};
