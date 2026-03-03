type Listener = () => void;

const listeners: Set<Listener> = new Set();

let pendingPath: string | null = null;

const notifyListeners = () => {
  listeners.forEach((listener) => listener());
};

const setPendingPath = (path: string) => {
  pendingPath = path;
  notifyListeners();
};

const consumePendingPath = (): string | null => {
  const path = pendingPath;
  pendingPath = null;
  return path;
};

const getPendingPath = (): string | null => pendingPath;

const subscribe = (listener: Listener) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

export const deepLinkStorage = {
  setPendingPath,
  consumePendingPath,
  getPendingPath,
  subscribe,
};
