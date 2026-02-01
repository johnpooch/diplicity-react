import React, { Suspense } from "react";
import { useNavigate } from "react-router";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useUserRetrieveSuspense } from "@/api/generated/endpoints";

const UserAvatarContent: React.FC = () => {
  const navigate = useNavigate();
  const { data: userProfile } = useUserRetrieveSuspense();

  const handleClick = () => {
    navigate("/profile");
  };

  return (
    <button
      onClick={handleClick}
      className="md:hidden"
      aria-label="Go to profile"
    >
      <Avatar className="size-8">
        <AvatarImage src={userProfile?.picture ?? undefined} />
        <AvatarFallback>
          {userProfile?.name?.[0]?.toUpperCase()}
        </AvatarFallback>
      </Avatar>
    </button>
  );
};

const UserAvatar: React.FC = () => {
  return (
    <Suspense fallback={null}>
      <UserAvatarContent />
    </Suspense>
  );
};

export { UserAvatar };
