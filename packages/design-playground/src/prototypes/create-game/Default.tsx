import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { ScreenContainer } from "@/components/ui/screen-container";
import { HomeShell } from "@/components/HomeShell";
import { ScreenHeader } from "@/components/ScreenHeader";
import { NationAvatar } from "@/components/NationAvatar";
import { StaticMap } from "@/components/StaticMap";
import { nations } from "@/data/fixtures";
import { Bot, Minus, Plus } from "lucide-react";

const bots = [
  { name: "dealmakerbot", blurb: "Talks first, moves second" },
  { name: "stonewallbot", blurb: "Defends everything, risks nothing" },
  { name: "opportunistbot", blurb: "Breaks alliances when it pays" },
];

const CreateGame: React.FC<{ state: string }> = ({ state }) => {
  const [botCount, setBotCount] = useState(state === "with-bots" ? 3 : 0);
  const humanSeats = nations.length - botCount;

  return (
    <HomeShell activeNavItem="Create Game">
      <ScreenContainer>
        <ScreenHeader title="Create Game" />

        <Card>
          <CardContent className="flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <Label htmlFor="name">Game name</Label>
              <Input id="name" defaultValue="The Congress of Vienna" />
            </div>

            <div className="flex gap-3">
              <div className="size-24 shrink-0 overflow-hidden rounded-md border bg-muted">
                <StaticMap />
              </div>
              <div className="flex flex-1 flex-col gap-2">
                <Label htmlFor="variant">Variant</Label>
                <Select defaultValue="classical">
                  <SelectTrigger id="variant">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="classical">Classical</SelectItem>
                    <SelectItem value="hundred">Hundred</SelectItem>
                    <SelectItem value="canton">Canton</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  7 nations · 34 supply centres
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="deadline">Phase deadline</Label>
              <Select defaultValue="24">
                <SelectTrigger id="deadline">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="12">12 hours</SelectItem>
                  <SelectItem value="24">24 hours</SelectItem>
                  <SelectItem value="48">48 hours</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between gap-4">
              <div>
                <Label htmlFor="private">Private game</Label>
                <p className="text-sm text-muted-foreground">
                  Only people with the link can join
                </p>
              </div>
              <Switch id="private" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex flex-col gap-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="flex items-center gap-2 font-semibold">
                  <Bot className="size-4" />
                  Fill empty seats with bots
                </h2>
                <p className="text-sm text-muted-foreground">
                  Bots take any seat still open when the game starts.
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="Fewer bots"
                  disabled={botCount === 0}
                  onClick={() => setBotCount(count => Math.max(0, count - 1))}
                >
                  <Minus />
                </Button>
                <span className="w-6 text-center tabular-nums">{botCount}</span>
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="More bots"
                  disabled={botCount === nations.length - 1}
                  onClick={() =>
                    setBotCount(count => Math.min(nations.length - 1, count + 1))
                  }
                >
                  <Plus />
                </Button>
              </div>
            </div>

            {botCount > 0 && (
              <>
                <Separator />
                <div className="flex flex-col gap-3">
                  {bots.slice(0, botCount).map((bot, index) => (
                    <div key={bot.name} className="flex items-center gap-3">
                      <NationAvatar nation={nations[humanSeats + index]} />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">
                          {bot.name}
                        </p>
                        <p className="truncate text-sm text-muted-foreground">
                          {bot.blurb}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            <p className="text-sm text-muted-foreground">
              {humanSeats} human {humanSeats === 1 ? "seat" : "seats"} ·{" "}
              {botCount} bot {botCount === 1 ? "seat" : "seats"}
            </p>
          </CardContent>
        </Card>

        <Button className="w-full" size="lg">
          Create game
        </Button>
      </ScreenContainer>
    </HomeShell>
  );
};

export { CreateGame };
