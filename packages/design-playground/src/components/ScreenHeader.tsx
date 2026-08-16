import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { CircleHelp } from "lucide-react";

interface ScreenHeaderProps {
  title: string;
  actions?: React.ReactNode;
}

const ScreenHeader: React.FC<ScreenHeaderProps> = ({ title, actions }) => {
  return (
    <div className="flex items-center justify-between gap-3">
      <h1 className="text-2xl font-bold">{title}</h1>
      <div className="flex items-center gap-6">
        {actions}
        <CircleHelp className="size-5 md:hidden" />
        <Avatar className="size-8 md:hidden">
          <AvatarFallback>O</AvatarFallback>
        </Avatar>
      </div>
    </div>
  );
};

export { ScreenHeader };
