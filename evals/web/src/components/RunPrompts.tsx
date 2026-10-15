import { Suspense } from "react";
import { useSearchParams } from "react-router-dom";
import { useRun, useRunPrompts, type FixturePrompts, type RunDetail, type RunSummary } from "@/api";
import { PromptDiff } from "@/components/PromptDiff";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatInterval, formatRun, formatScore, plural } from "@/labels";
import { compareRuns, sharedFixtures, type Side } from "@/runComparison";
import { usable } from "@/stats";

interface RunPromptsProps {
  run: RunDetail;
  others: RunSummary[];
}

interface PromptsProps {
  prompts: FixturePrompts[];
  before: FixturePrompts[] | null;
}

interface ComparedProps {
  run: RunDetail;
  prompts: FixturePrompts[];
  against: string;
}

interface ComparisonProps {
  run: RunDetail;
  other: RunDetail;
}

const NOTHING = "nothing";

const describeSide = (side: Side): string =>
  `${formatScore(side.score)} (${formatInterval(side.interval)}, ${plural(usable(side), "answer")})`;

const Prompts: React.FC<PromptsProps> = ({ prompts, before }) => {
  const [params, setParams] = useSearchParams();
  const shown = before === null ? prompts : prompts.filter(own => before.some(other => other.fixture === own.fixture));
  const current = shown.find(own => own.fixture === params.get("fixture")) ?? shown[0];
  const earlier = before?.find(other => other.fixture === current?.fixture);

  const setFixture = (fixture: string) => {
    const next = new URLSearchParams(params);
    next.set("fixture", fixture);
    setParams(next, { replace: true });
  };

  if (!current) {
    return <p className="text-sm text-muted-foreground">This run sent no prompts.</p>;
  }

  return (
    <>
      {shown.length > 1 && (
        <label className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Fixture</span>
          <Select value={current.fixture} onValueChange={setFixture}>
            <SelectTrigger size="sm" aria-label="Fixture">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {shown.map(own => (
                <SelectItem key={own.fixture} value={own.fixture}>
                  {own.fixture}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>
      )}
      <PromptDiff
        key={`system:${current.fixture}`}
        title="System prompt"
        before={earlier ? (earlier.system ?? "") : null}
        after={current.system ?? ""}
      />
      <PromptDiff
        key={`user:${current.fixture}`}
        title="User prompt"
        before={earlier ? (earlier.user ?? "") : null}
        after={current.user ?? ""}
      />
    </>
  );
};

const Comparison: React.FC<ComparisonProps> = ({ run, other }) => {
  const comparison = compareRuns(run, other);
  if (!comparison) {
    return (
      <p className="text-sm text-muted-foreground">The two runs share no fixture, so their scores are not compared.</p>
    );
  }

  const verdict =
    comparison.overlapping === null
      ? "One side has no usable answer, so there is nothing to compare."
      : comparison.overlapping
        ? "The intervals overlap, so this is not a clear difference."
        : "The intervals do not overlap.";

  return (
    <div className="flex flex-col gap-1 rounded-md bg-muted/60 px-3 py-2 text-sm">
      <p>
        On the {plural(comparison.fixtures.length, "fixture")} both runs cover: {describeSide(comparison.here)}{" "}
        here, {describeSide(comparison.there)} there. {verdict}
      </p>
      {run.model !== other.model && (
        <p className="text-muted-foreground">
          The models differ ({run.model} here, {other.model} there), so the prompt is not the only change.
        </p>
      )}
      {run.prompt !== null && run.prompt === other.prompt && (
        <p className="text-muted-foreground">Both runs sent the same prompt.</p>
      )}
    </div>
  );
};

const Compared: React.FC<ComparedProps> = ({ run, prompts, against }) => {
  const { data: other } = useRun(against);
  const { data: before } = useRunPrompts(against);
  return (
    <>
      <Comparison run={run} other={other} />
      <Prompts prompts={prompts} before={before} />
    </>
  );
};

export const RunPrompts: React.FC<RunPromptsProps> = ({ run, others }) => {
  const { data: prompts } = useRunPrompts(run.name);
  const [params, setParams] = useSearchParams();
  const own = run.fixtures.map(fixture => fixture.id);
  const candidates = others.filter(other => sharedFixtures(own, other.fixture_ids).length > 0);
  const against = candidates.find(other => other.name === params.get("against"));

  const setAgainst = (name: string) => {
    const next = new URLSearchParams(params);
    if (name === NOTHING) {
      next.delete("against");
    } else {
      next.set("against", name);
    }
    setParams(next, { replace: true });
  };

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-semibold">
          Prompt
          <span className="ml-2 font-mono text-sm font-normal text-muted-foreground">{run.prompt ?? "unknown"}</span>
        </h2>
        <label className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Compare with</span>
          <Select value={against?.name ?? NOTHING} onValueChange={setAgainst} disabled={candidates.length === 0}>
            <SelectTrigger size="sm" aria-label="Compare with">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={NOTHING}>
                {candidates.length > 0 ? "Nothing" : "No other run covers these fixtures"}
              </SelectItem>
              {candidates.map(other => (
                <SelectItem key={other.name} value={other.name}>
                  {formatRun(other.created)} · {other.prompt ?? "unknown"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </label>
      </div>
      {against ? (
        <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
          <Compared key={against.name} run={run} prompts={prompts} against={against.name} />
        </Suspense>
      ) : (
        <Prompts prompts={prompts} before={null} />
      )}
    </section>
  );
};
