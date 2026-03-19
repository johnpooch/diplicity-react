import { useState, useCallback } from "react";

const useDraft = (
  gameId: string,
  channelId: string
): [string, (value: string) => void] => {
  const key = `draft:${gameId}:${channelId}`;

  const [draft, setDraftState] = useState(
    () => sessionStorage.getItem(key) ?? ""
  );

  const setDraft = useCallback(
    (value: string) => {
      setDraftState(value);
      if (value) {
        sessionStorage.setItem(key, value);
      } else {
        sessionStorage.removeItem(key);
      }
    },
    [key]
  );

  return [draft, setDraft];
};

export { useDraft };
