import React, { Suspense } from "react";
import { useNavigate } from "react-router";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useUserRetrieveSuspense } from "@/api/generated/endpoints";
import { tokenStorage } from "@/auth/tokenStorage";

const UserAvatarContent: React.FC = () => {
  const navigate = useNavigate();
  const { data: userProfile } = useUserRetrieveSuspense();

  const handleClick = () => {
    navigate("/account");
  };

  return (
    <button
      onClick={handleClick}
      className="md:hidden"
      aria-label="Go to account"
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
  if (!tokenStorage.isLoggedIn()) {
    return null;
  }
  return (
    <Suspense fallback={null}>
      <UserAvatarContent />
    </Suspense>
  );
};

export { UserAvatar };
