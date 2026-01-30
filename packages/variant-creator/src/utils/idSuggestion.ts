export function suggestId(name: string): string {
  const trimmed = name.trim().toLowerCase();
  if (!trimmed) return "";

  const words = trimmed.split(/\s+/);

  if (words.length === 1) {
    return words[0].slice(0, 3);
  }

  const initials = words.map((w) => w[0] || "").join("");

  if (initials.length >= 3) {
    return initials.slice(0, 3);
  }

  if (initials.length === 2) {
    return initials + words[words.length - 1].slice(1, 2);
  }

  return words[0].slice(0, 3);
}

export function validateProvinceId(id: string): {
  valid: boolean;
  error?: string;
} {
  if (!id) {
    return { valid: false, error: "ID is required" };
  }

  if (id.length !== 3) {
    return { valid: false, error: "ID must be exactly 3 characters" };
  }

  if (!/^[a-z]{3}$/.test(id)) {
    return { valid: false, error: "ID must be 3 lowercase letters" };
  }

  return { valid: true };
}

export function isUniqueId(id: string, existingIds: string[], currentId?: string): boolean {
  return !existingIds.some((existing) => existing === id && existing !== currentId);
}
