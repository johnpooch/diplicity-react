const ALLOWED_HOSTS = ["diplicity.com", "www.diplicity.com"];

export const parseDeepLinkUrl = (url: string): string | null => {
  try {
    const parsed = new URL(url);

    if (parsed.protocol === "diplicity:") {
      // URL API treats diplicity://game/123 as hostname=game, pathname=/123
      // Reconstruct the full path from hostname + pathname
      const fullPath = parsed.hostname
        ? "/" + parsed.hostname + parsed.pathname
        : "/" + parsed.pathname.replace(/^\/+/, "");
      return fullPath + parsed.search + parsed.hash;
    }

    if (
      (parsed.protocol === "https:" || parsed.protocol === "http:") &&
      ALLOWED_HOSTS.includes(parsed.hostname)
    ) {
      return parsed.pathname + parsed.search + parsed.hash;
    }

    return null;
  } catch {
    return null;
  }
};
