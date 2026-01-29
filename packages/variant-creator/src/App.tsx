import { Button } from "@/components/ui/button";

function App() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="mb-4 text-4xl font-bold">Diplicity Variant Creator</h1>
        <p className="mb-8 text-lg text-muted-foreground">
          Create custom Diplomacy variants using Inkscape SVG files. Upload your
          map, define provinces and nations, and export a complete variant
          definition.
        </p>
        <Button size="lg">Get Started</Button>
      </div>
    </div>
  );
}

export default App;
