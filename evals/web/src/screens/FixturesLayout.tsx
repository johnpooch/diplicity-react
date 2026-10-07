import { Suspense } from "react";
import { Navigate, NavLink, Outlet, useParams, useSearchParams } from "react-router-dom";
import { Inbox } from "lucide-react";
import { useFixtures } from "@/api";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export const FixturesLayout: React.FC = () => {
  const { data: fixtures } = useFixtures();
  const { fixtureId } = useParams();
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";

  if (fixtures.length === 0) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Inbox />
          </EmptyMedia>
          <EmptyTitle>No fixtures</EmptyTitle>
          <EmptyDescription>No fixture in evals/fixtures belongs to the eval set.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }
  if (!fixtureId) {
    return <Navigate to={`/fixtures/${fixtures[0].id}`} replace />;
  }

  const needle = query.trim().toLowerCase();
  const visible = fixtures.filter(fixture =>
    `${fixture.id} ${fixture.nation} ${fixture.phase.season} ${fixture.phase.year}`.toLowerCase().includes(needle)
  );

  return (
    <div className="flex h-full">
      <aside className="flex w-64 shrink-0 flex-col gap-2 overflow-y-auto border-r p-3">
        <Input
          type="search"
          placeholder="Search fixtures"
          aria-label="Search fixtures"
          value={query}
          onChange={event => setParams(event.target.value ? { q: event.target.value } : {}, { replace: true })}
        />
        <ul className="flex flex-col gap-0.5">
          {visible.map(fixture => (
            <li key={fixture.id}>
              <NavLink
                to={{ pathname: `/fixtures/${fixture.id}`, search: params.toString() }}
                className={({ isActive }) =>
                  cn("flex flex-col rounded-md px-2 py-1.5 text-sm hover:bg-accent", isActive && "bg-accent")
                }
              >
                <span className="truncate font-medium">{fixture.id}</span>
                <span className="text-xs text-muted-foreground">
                  {fixture.nation} · {fixture.phase.season} {fixture.phase.year}
                </span>
              </NavLink>
            </li>
          ))}
        </ul>
        {visible.length === 0 && <p className="px-2 text-sm text-muted-foreground">No fixture matches.</p>}
      </aside>
      <div className="min-w-0 flex-1">
        <Suspense fallback={<p className="p-6 text-sm text-muted-foreground">Loading…</p>}>
          <Outlet />
        </Suspense>
      </div>
    </div>
  );
};
