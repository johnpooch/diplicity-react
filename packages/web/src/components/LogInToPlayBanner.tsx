import { useLocation, useNavigate } from "react-router";
import { LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/Notice";
import { deepLinkStorage } from "@/deepLink";

const LogInToPlayBanner: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogIn = () => {
    deepLinkStorage.setPendingPath(location.pathname + location.search);
    navigate("/");
  };

  return (
    <Notice
      icon={LogIn}
      title="Log in to play"
      message="Sign in to submit orders, chat with other players, and join games."
      actions={<Button onClick={handleLogIn}>Log in</Button>}
    />
  );
};

export { LogInToPlayBanner };
