import { cn } from "@/lib/utils";

interface DiplicityLogoProps {
  className?: string;
}

const DiplicityLogo: React.FC<DiplicityLogoProps> = ({ className }) => {
  return (
    <img
      src="/otto.png"
      alt="Diplicity"
      className={cn("size-8", className)}
    />
  );
};

export { DiplicityLogo };
