import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

const nationColours: Record<string, string> = {
  Austria: "bg-red-200 text-red-900",
  England: "bg-purple-200 text-purple-900",
  France: "bg-sky-200 text-sky-900",
  Germany: "bg-stone-300 text-stone-900",
  Italy: "bg-green-200 text-green-900",
  Russia: "bg-fuchsia-200 text-fuchsia-900",
  Turkey: "bg-amber-200 text-amber-900",
};

interface NationAvatarProps {
  nation: string;
  className?: string;
}

const NationAvatar: React.FC<NationAvatarProps> = ({ nation, className }) => {
  return (
    <Avatar className={cn("size-8", className)}>
      <AvatarFallback
        className={cn("text-xs font-semibold", nationColours[nation])}
      >
        {nation.slice(0, 2).toUpperCase()}
      </AvatarFallback>
    </Avatar>
  );
};

export { NationAvatar, nationColours };
