import { cn } from "@/lib/utils";
import { nationColours } from "@/components/NationAvatar";

const flagSrc: Record<string, string> = {
  Austria: "/flags/austria.svg",
  England: "/flags/england.svg",
  France: "/flags/france.svg",
  Germany: "/flags/germany.svg",
  Italy: "/flags/italy.svg",
  Russia: "/flags/russia.svg",
  Turkey: "/flags/turkey.svg",
};

interface NationFlagProps {
  nation: string;
  className?: string;
}

const NationFlag: React.FC<NationFlagProps> = ({ nation, className }) => {
  const src = flagSrc[nation];

  if (src) {
    return (
      <img
        src={src}
        alt={nation}
        className={cn("size-full rounded-full object-cover", className)}
      />
    );
  }

  return (
    <span
      aria-label={nation}
      className={cn(
        "flex size-full items-center justify-center rounded-full text-[8px] font-semibold",
        nationColours[nation] ?? "bg-muted text-muted-foreground",
        className
      )}
    >
      {nation.slice(0, 2).toUpperCase()}
    </span>
  );
};

export { NationFlag };
