import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

type MessageProps = {
  children: React.ReactNode;
  className?: string;
} & React.HTMLAttributes<HTMLDivElement>;

const Message = ({ children, className, ...props }: MessageProps) => (
  <div className={cn("flex gap-3", className)} {...props}>
    {children}
  </div>
);

type MessageAvatarProps = {
  src?: string;
  alt: string;
  fallback?: string;
  delayMs?: number;
  className?: string;
};

const MessageAvatar = ({
  src,
  alt,
  fallback,
  delayMs,
  className,
}: MessageAvatarProps) => (
  <Avatar className={cn("h-8 w-8 shrink-0", className)}>
    <AvatarImage src={src} alt={alt} />
    {fallback && <AvatarFallback delayMs={delayMs}>{fallback}</AvatarFallback>}
  </Avatar>
);

type MessageContentProps = {
  children: React.ReactNode;
  className?: string;
} & React.HTMLAttributes<HTMLDivElement>;

const MessageContent = ({
  children,
  className,
  ...props
}: MessageContentProps) => (
  <div
    className={cn(
      "rounded-lg p-2 text-foreground bg-secondary break-words whitespace-normal",
      className
    )}
    {...props}
  >
    {children}
  </div>
);

type MessageTimestampProps = {
  children: React.ReactNode;
  className?: string;
} & React.HTMLAttributes<HTMLDivElement>;

const MessageTimestamp = ({
  children,
  className,
  ...props
}: MessageTimestampProps) => (
  <div
    className={cn("text-xs text-muted-foreground text-right mt-1", className)}
    {...props}
  >
    {children}
  </div>
);

export { Message, MessageAvatar, MessageContent, MessageTimestamp };
