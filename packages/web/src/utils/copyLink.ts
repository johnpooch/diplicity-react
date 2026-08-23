import { toast } from "sonner";

const APP_ORIGIN = "https://diplicity.com";

export const copyLink = async (path: string) => {
  try {
    await navigator.clipboard.writeText(`${APP_ORIGIN}${path}`);
    toast.success("Link copied to clipboard");
  } catch {
    toast.error("Failed to copy link");
  }
};
