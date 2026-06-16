import { useEffect, useState } from "react";
import { Send } from "lucide-react";
import type { Nation } from "@/api/generated/endpoints";
import {
  Message,
  MessageAvatar,
  MessageContent,
} from "@/components/ui/message";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ScriptedMessage } from "../types";

interface ScriptedChatProps {
  script: ScriptedMessage[];
  you: Nation;
  ally: Nation;
  continueLabel: string;
  onContinue: () => void;
}

const REPLY_DELAY_MS = 1100;

const ScriptedChat: React.FC<ScriptedChatProps> = ({
  script,
  you,
  ally,
  continueLabel,
  onContinue,
}) => {
  const [revealed, setRevealed] = useState(0);

  const next = script[revealed];
  const allyIsReplying = next?.from === "ally";
  const canSend = next?.from === "you";
  const done = revealed >= script.length;

  // Ally replies arrive on their own after a short delay.
  useEffect(() => {
    if (!allyIsReplying) return;
    const timer = setTimeout(() => setRevealed(r => r + 1), REPLY_DELAY_MS);
    return () => clearTimeout(timer);
  }, [allyIsReplying, revealed]);

  return (
    <div
      className={cn(
        "absolute z-20 flex flex-col bg-background text-foreground",
        "inset-0",
        "md:inset-y-0 md:left-0 md:right-auto md:w-[400px] md:border-r"
      )}
    >
      <div className="border-b p-4">
        <span className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
          Press · {ally.name}
        </span>
        <p className="mt-1 text-sm text-muted-foreground">
          Tap your reply to send it.
        </p>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {script.slice(0, revealed).map((message, index) => {
          const nation = message.from === "you" ? you : ally;
          const isYou = message.from === "you";
          return (
            <Message
              key={index}
              className={isYou ? "flex-row-reverse" : undefined}
            >
              <MessageAvatar
                alt={nation.name}
                src={nation.flagUrl ?? undefined}
                fallback={nation.name.slice(0, 2)}
              />
              <MessageContent
                className={isYou ? "rounded-tr-none" : "rounded-tl-none"}
                style={{ backgroundColor: `${nation.color}33` }}
              >
                <span
                  className="mb-0.5 block text-xs font-semibold"
                  style={{ color: nation.color }}
                >
                  {nation.name}
                </span>
                {message.body}
              </MessageContent>
            </Message>
          );
        })}
        {allyIsReplying && (
          <span className="block text-xs text-muted-foreground">
            {ally.name} is typing…
          </span>
        )}
      </div>

      <div className="border-t p-4">
        {canSend && (
          <Button
            className="h-auto w-full justify-start whitespace-normal py-2 text-left"
            variant="outline"
            onClick={() => setRevealed(r => r + 1)}
          >
            <Send className="shrink-0" />
            {next.body}
          </Button>
        )}
        {done && (
          <Button className="w-full" onClick={onContinue}>
            {continueLabel}
          </Button>
        )}
      </div>
    </div>
  );
};

export { ScriptedChat };
