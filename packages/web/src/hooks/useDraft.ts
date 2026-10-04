import { useState, useCallback } from "react";

const createDraftId = () => {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
};

const useDraft = (
  gameId: string,
  channelId: string
): [string, (value: string) => void, string | null] => {
  const key = `draft:${gameId}:${channelId}`;
  const idKey = `draft-id:${gameId}:${channelId}`;

  const [draft, setDraftState] = useState(
    () => sessionStorage.getItem(key) ?? ""
  );
  const [draftId, setDraftId] = useState(() =>
    draft ? (sessionStorage.getItem(idKey) ?? createDraftId()) : null
  );

  const setDraft = useCallback(
    (value: string) => {
      setDraftState(value);
      if (value) {
        const id = createDraftId();
        setDraftId(id);
        sessionStorage.setItem(key, value);
        sessionStorage.setItem(idKey, id);
      } else {
        setDraftId(null);
        sessionStorage.removeItem(key);
        sessionStorage.removeItem(idKey);
      }
    },
    [key, idKey]
  );

  return [draft, setDraft, draftId];
};

export { useDraft };
