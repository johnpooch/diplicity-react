import React, { useRef, useState } from "react";
import { AxiosError } from "axios";
import { Camera, Loader2, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { downscaleImage } from "@/utils/downscaleImage";
import {
  useUserPictureUpdate,
  useUserPictureDestroy,
  getUserRetrieveQueryKey,
  getUsersRetrieveQueryKey,
  UserProfilePicture,
} from "@/api/generated/endpoints";

const pictureErrorMessage = (error: unknown, fallback: string) => {
  const data = (error as AxiosError<{ picture?: string[]; detail?: string }>)
    .response?.data;
  return data?.picture?.[0] ?? data?.detail ?? fallback;
};

interface ProfilePictureEditorProps {
  userId: number;
  name: string;
  picture: string | null;
}

export const ProfilePictureEditor: React.FC<ProfilePictureEditorProps> = ({
  userId,
  name,
  picture,
}) => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadPictureMutation = useUserPictureUpdate();
  const removePictureMutation = useUserPictureDestroy();
  const [isUploading, setIsUploading] = useState(false);
  const isPending = isUploading || removePictureMutation.isPending;

  const refreshProfile = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: getUserRetrieveQueryKey() }),
      queryClient.invalidateQueries({
        queryKey: getUsersRetrieveQueryKey(userId),
      }),
    ]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const picture = await downscaleImage(file);
      await uploadPictureMutation.mutateAsync({
        data: { picture: picture as unknown as UserProfilePicture["picture"] },
      });
      await refreshProfile();
    } catch (error) {
      toast.error(pictureErrorMessage(error, "Failed to upload picture"));
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemove = async () => {
    try {
      await removePictureMutation.mutateAsync();
      await refreshProfile();
    } catch (error) {
      toast.error(pictureErrorMessage(error, "Failed to remove picture"));
    }
  };

  return (
    <div className="relative">
      <Avatar className="size-16">
        <AvatarImage src={picture ?? undefined} />
        <AvatarFallback className="text-xl">
          {name[0]?.toUpperCase()}
        </AvatarFallback>
      </Avatar>
      {isPending && (
        <div className="absolute inset-0 flex items-center justify-center rounded-full bg-background/70">
          <Loader2 className="size-4 animate-spin" />
        </div>
      )}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            size="icon"
            variant="secondary"
            disabled={isPending}
            aria-label="Change picture"
            className="absolute -bottom-1 -right-1 size-6 rounded-full border"
          >
            <Camera className="size-3" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem onSelect={() => fileInputRef.current?.click()}>
            <Upload />
            {picture ? "Replace picture" : "Upload picture"}
          </DropdownMenuItem>
          {picture && (
            <DropdownMenuItem variant="destructive" onSelect={handleRemove}>
              <Trash2 />
              Remove picture
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        tabIndex={-1}
        aria-hidden
        onChange={event => {
          const file = event.target.files?.[0];
          if (file) handleUpload(file);
          event.target.value = "";
        }}
      />
    </div>
  );
};
