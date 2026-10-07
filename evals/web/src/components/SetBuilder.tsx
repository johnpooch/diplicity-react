import type { FixtureDetail } from "@/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface SetBuilderProps {
  fixture: FixtureDetail;
  draft: Record<string, string>;
  onChange: (draft: Record<string, string>) => void;
}

const NO_ORDER = "none";

export const SetBuilder: React.FC<SetBuilderProps> = ({ fixture, draft, onChange }) => {
  const groups = new Map<string, string[]>();
  for (const id of fixture.options) {
    const source = fixture.orders[id].source;
    groups.set(source, [...(groups.get(source) ?? []), id]);
  }

  const choose = (source: string, id: string) => {
    const next = { ...draft };
    if (id === NO_ORDER) {
      delete next[source];
    } else {
      next[source] = id;
    }
    onChange(next);
  };

  return (
    <div className="flex flex-col gap-2">
      {fixture.max_orders !== null && (
        <p className="text-xs text-muted-foreground">At most {fixture.max_orders} order(s) this phase.</p>
      )}
      {[...groups].map(([source, options]) => (
        <div key={source} className="flex items-center gap-2 text-sm">
          <span className="w-28 shrink-0 truncate">{fixture.orders[options[0]].source_name}</span>
          <Select value={draft[source] ?? NO_ORDER} onValueChange={id => choose(source, id)}>
            <SelectTrigger
              size="sm"
              className="min-w-0 flex-1"
              aria-label={fixture.orders[options[0]].source_name}
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={NO_ORDER}>No order</SelectItem>
              {options.map(id => (
                <SelectItem key={id} value={id}>
                  {fixture.orders[id].description}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      ))}
    </div>
  );
};
