import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { DiplicityLogo } from "@/components/DiplicityLogo";
import { prototypes } from "@/manifest";

const Index: React.FC = () => {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <header className="mb-8 flex items-center gap-3">
        <DiplicityLogo />
        <div>
          <h1 className="text-2xl font-bold">Design Playground</h1>
          <p className="text-sm text-muted-foreground">
            Clickable prototypes. Nothing here is real, and nothing here ships.
          </p>
        </div>
      </header>

      <div className="flex flex-col gap-4">
        {prototypes.map(prototype => (
          <Card key={prototype.slug}>
            <CardContent className="flex flex-col gap-4">
              <div>
                <h2 className="text-lg font-semibold">{prototype.title}</h2>
                <p className="text-sm text-muted-foreground">
                  {prototype.description}
                </p>
              </div>

              <Separator />

              <div className="flex flex-col gap-4">
                {prototype.variants.map(variant => (
                  <div key={variant.slug} className="flex flex-col gap-2">
                    <div>
                      <Link
                        to={`/${prototype.slug}/${variant.slug}`}
                        className="font-medium underline underline-offset-4"
                      >
                        {variant.title}
                      </Link>
                      <p className="text-sm text-muted-foreground">
                        {variant.description}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {variant.states.map(state => (
                        <Link
                          key={state.slug}
                          to={`/${prototype.slug}/${variant.slug}/${state.slug}`}
                        >
                          <Badge variant="secondary">{state.title}</Badge>
                        </Link>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export { Index };
