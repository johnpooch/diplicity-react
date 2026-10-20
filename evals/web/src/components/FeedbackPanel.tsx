import { useRef, useState } from "react";
import { useSaveNote, type Game, type GamePhase } from "@/api";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { mergeNotes, OVERALL, phaseLabel, stitchNotes } from "@/games";
import { cn } from "@/lib/utils";

interface FeedbackPanelProps {
  game: Game;
  phase: GamePhase;
}

type Status = "saved" | "saving" | "error";

const SAVE_DELAY = 600;

const STATUS: Record<Status, string> = {
  saved: "Saved",
  saving: "Saving…",
  error: "Not saved",
};

export const FeedbackPanel: React.FC<FeedbackPanelProps> = ({ game, phase }) => {
  const save = useSaveNote(game.name, game.seed);
  const [tab, setTab] = useState<string>("phase");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<Status>("saved");
  const [problem, setProblem] = useState<string | null>(null);
  const timers = useRef(new Map<string, number>());

  const key = tab === OVERALL ? OVERALL : phase.key;
  const notes = mergeNotes(game.feedback, drafts);
  const value = key === OVERALL ? notes.overall : (notes.phases[key] ?? "");
  const stitched = stitchNotes(notes, game.phases);

  const onChange = (text: string) => {
    setDrafts(current => ({ ...current, [key]: text }));
    setStatus("saving");
    window.clearTimeout(timers.current.get(key));
    timers.current.set(
      key,
      window.setTimeout(() => {
        timers.current.delete(key);
        save
          .mutateAsync({ phase: key === OVERALL ? null : key, note: text })
          .then(() => {
            setProblem(null);
            setStatus(timers.current.size > 0 ? "saving" : "saved");
          })
          .catch((error: Error) => {
            setProblem(error.message);
            setStatus("error");
          });
      }, SAVE_DELAY)
    );
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">Feedback</h2>
        <span
          className={cn("text-xs", status === "error" ? "text-destructive" : "text-muted-foreground")}
          title={problem ?? undefined}
          aria-live="polite"
        >
          {STATUS[status]}
        </span>
      </div>
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="w-full">
          <TabsTrigger value="phase">{phaseLabel(phase.phase)}</TabsTrigger>
          <TabsTrigger value={OVERALL}>Overall</TabsTrigger>
        </TabsList>
      </Tabs>
      <Textarea
        key={key}
        value={value}
        onChange={event => onChange(event.target.value)}
        placeholder={key === OVERALL ? "What should change about how it plays?" : "What went right or wrong this phase?"}
        aria-label={key === OVERALL ? "Overall note" : `Note on ${phaseLabel(phase.phase)}`}
        className="min-h-32"
      />
      {problem && <p className="text-xs text-destructive">{problem}</p>}
      <section className="flex min-h-0 flex-1 flex-col gap-2">
        <h3 className="text-xs font-medium text-muted-foreground">All notes</h3>
        {stitched.length === 0 ? (
          <p className="text-sm text-muted-foreground">No notes on this game yet.</p>
        ) : (
          <div className="min-h-0 overflow-y-auto rounded-md bg-muted/60 px-3 py-2 text-sm">
            {stitched.map(note => (
              <p key={note.key} className="mb-3 whitespace-pre-wrap last:mb-0">
                <span className="font-medium">{note.heading}</span> {note.text}
              </p>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
