import React from "react";
import { SearchX } from "lucide-react";
import { DiplicityLogo } from "./DiplicityLogo";
import { PrimaryButton, SecondaryButton } from "@/components/ui/role-buttons";
import { SafeAreaView } from "@/components/SafeAreaView";
import { Notice } from "@/components/Notice";

const goHome = () => {
  window.location.href = "/";
};

const title = "This game is no longer available";
const message = "It may have been deleted.";

interface NotFoundNoticeProps {
  fullScreen?: boolean;
}

const NotFoundNotice: React.FC<NotFoundNoticeProps> = ({ fullScreen }) => {
  if (fullScreen) {
    return (
      <div className="max-w-sm mx-auto">
        <SafeAreaView className="flex flex-col items-center justify-center min-h-screen text-center gap-6">
          <DiplicityLogo />
          <h1 className="text-2xl font-bold text-center">{title}</h1>
          <p className="text-muted-foreground">{message}</p>
          <SecondaryButton onClick={goHome}>Go to my games</SecondaryButton>
        </SafeAreaView>
      </div>
    );
  }

  return (
    <Notice
      icon={SearchX}
      title={title}
      message={message}
      actions={<PrimaryButton onClick={goHome}>Go to my games</PrimaryButton>}
    />
  );
};

export { NotFoundNotice };
