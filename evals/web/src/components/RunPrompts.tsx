import { useSearchParams } from "react-router-dom";
import { useRunPrompts, type FixturePrompts, type RunHeader } from "@/api";
import { PromptDiff } from "@/components/PromptDiff";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatRun } from "@/labels";

interface RunPromptsProps {
  run: string;
  others: RunHeader[];
  previous: RunHeader | undefined;
}

interface PromptsProps {
  prompts: FixturePrompts[];
  before: FixturePrompts[] | null;
}

interface ComparedProps {
  prompts: FixturePrompts[];
  against: string;
}

const Prompts: React.FC<PromptsProps> = ({ prompts, before }) => {
  const [params, setParams] = useSearchParams();
  const shared = before === null ? prompts : prompts.filter(own => before.some(other => other.fixture === own.fixture));
  const current = shared.find(own => own.fixture === params.get("fixture")) ?? shared[0];
  const earlier = before?.find(other => other.fixture === current?.fixture);

  const setFixture = (fixture: string) => {
    const next = new URLSearchParams(params);
    next.set("fixture", fixture);
    setParams(next, { replace: true });
  };

  if (!current) {
    return <p className="text-sm text-muted-foreground">The two runs share no fixture to compare.</p>;
  }

  return (
    <>
      {shared.length > 1 && (
        <label className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Fixture</span>
          <Select value={current.fixture} onValueChange={setFixture}>
            <SelectTrigger size="sm" aria-label="Fixture">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {shared.map(own => (
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

const Compared: React.FC<ComparedProps> = ({ prompts, against }) => {
  const { data: before } = useRunPrompts(against);
  return <Prompts prompts={prompts} before={before} />;
};

export const RunPrompts: React.FC<RunPromptsProps> = ({ run, others, previous }) => {
  const { data: prompts } = useRunPrompts(run);
  const [params, setParams] = useSearchParams();
  const against = others.find(other => other.name === params.get("against")) ?? previous;

  const setAgainst = (name: string) => {
    const next = new URLSearchParams(params);
    next.set("against", name);
    setParams(next, { replace: true });
  };

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-semibold">Prompts</h2>
        {against && (
          <label className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Compared with</span>
            <Select value={against.name} onValueChange={setAgainst}>
              <SelectTrigger size="sm" aria-label="Compared with">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {others.map(other => (
                  <SelectItem key={other.name} value={other.name}>
                    {formatRun(other.created)}
                    {other.name === previous?.name ? " (previous)" : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>
        )}
      </div>
      {against ? (
        <Compared key={against.name} prompts={prompts} against={against.name} />
      ) : (
        <Prompts prompts={prompts} before={null} />
      )}
    </section>
  );
};
