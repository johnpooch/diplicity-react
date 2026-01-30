import { useNavigate, useParams, Navigate } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useVariant } from "@/hooks/useVariant";
import { WIZARD_PHASES } from "@/Router";

const PHASE_TITLES = [
  "Variant Setup",
  "Province Details",
  "Text Association",
  "Adjacencies",
  "Visual Editor",
  "Review & Export",
];

interface WizardLayoutProps {
  children: React.ReactNode;
}

export function WizardLayout({ children }: WizardLayoutProps) {
  const navigate = useNavigate();
  const { "*": phaseParam } = useParams();
  const { variant } = useVariant();

  const currentPhase = parseInt(phaseParam || "0", 10);
  const totalPhases = PHASE_TITLES.length;

  if (!variant) {
    return <Navigate to="/" replace />;
  }

  const canGoNext = currentPhase < WIZARD_PHASES.length - 1;

  const handlePrevious = () => {
    if (currentPhase === 0) {
      navigate("/");
    } else {
      navigate(`/phase/${currentPhase - 1}`);
    }
  };

  const handleNext = () => {
    if (canGoNext) {
      navigate(`/phase/${currentPhase + 1}`);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={handlePrevious}
              className="gap-1"
            >
              <ChevronLeft className="h-4 w-4" />
              {currentPhase === 0 ? "Home" : "Previous"}
            </Button>
          </div>

          <div className="flex flex-col items-center">
            <span className="text-sm font-medium">
              {PHASE_TITLES[currentPhase]}
            </span>
            <span className="text-xs text-muted-foreground">
              Phase {currentPhase + 1} of {totalPhases}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleNext}
              disabled={!canGoNext}
              className="gap-1"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="mx-auto max-w-5xl px-4 pb-2">
          <div className="flex gap-1">
            {Array.from({ length: totalPhases }).map((_, i) => (
              <div
                key={i}
                className={`h-1 flex-1 rounded-full transition-colors ${
                  i <= currentPhase ? "bg-primary" : "bg-muted"
                }`}
              />
            ))}
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto max-w-5xl px-4 py-6">{children}</div>
      </main>
    </div>
  );
}
