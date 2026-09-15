import { NationFlag } from "@/components/NationFlag";

interface NationAvatarProps {
  nation: string;
  className?: string;
}

const NationAvatar: React.FC<NationAvatarProps> = ({ nation, className }) => {
  return <NationFlag nation={nation} size="md" className={className} />;
};

export { NationAvatar };
