import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="flex w-full max-w-md flex-col items-center gap-8 text-center">
        <div>
          <h1 className="mb-2 text-4xl font-bold">Diplicity Tools</h1>
          <p className="text-muted-foreground">
            Choose a tool to get started.
          </p>
        </div>

        <div className="flex w-full flex-col gap-4">
          <Button size="lg" className="w-full" onClick={() => navigate("/variant-creator")}>
            Variant Creator
          </Button>
          <Button size="lg" variant="outline" className="w-full" onClick={() => navigate("/dsvg-creator")}>
            dSVG Creator
          </Button>
        </div>
      </div>
    </div>
  );
}
