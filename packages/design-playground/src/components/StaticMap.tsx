import { cn } from "@/lib/utils";

interface StaticMapProps {
  className?: string;
}

const StaticMap: React.FC<StaticMapProps> = ({ className }) => {
  return (
    <img
      src="/classical-board.svg"
      alt="Classical map"
      className={cn("w-full h-full object-contain", className)}
    />
  );
};

export { StaticMap };
