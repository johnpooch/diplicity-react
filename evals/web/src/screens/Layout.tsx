import { Suspense } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { cn } from "@/lib/utils";

const SECTIONS = [
  { to: "/fixtures", name: "Fixtures" },
  { to: "/runs", name: "Runs" },
];

export const Layout: React.FC = () => (
  <div className="flex h-full flex-col">
    <header className="flex h-12 shrink-0 items-center gap-8 border-b px-6">
      <span className="font-semibold">Order evals</span>
      <nav className="flex gap-6 text-sm">
        {SECTIONS.map(section => (
          <NavLink
            key={section.to}
            to={section.to}
            className={({ isActive }) =>
              cn("text-muted-foreground hover:text-foreground", isActive && "font-medium text-foreground")
            }
          >
            {section.name}
          </NavLink>
        ))}
      </nav>
    </header>
    <main className="min-h-0 flex-1">
      <Suspense fallback={<p className="p-6 text-sm text-muted-foreground">Loading…</p>}>
        <Outlet />
      </Suspense>
    </main>
  </div>
);
