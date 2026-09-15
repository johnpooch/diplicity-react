import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, it, expect, vi } from "vitest";

const SCOPE = "https://diplicity.com/";
const LINK = "https://diplicity.com/game/1/phase/2/player-info";

const loadHandler = () => {
  const source = readFileSync(
    resolve(__dirname, "../public/firebase-messaging-sw.js"),
    "utf8"
  );
  let handler: ((event: unknown) => void) | undefined;
  const self = {
    registration: { scope: SCOPE },
    addEventListener: (type: string, listener: (event: unknown) => void) => {
      if (type === "notificationclick") handler = listener;
    },
  };
  const clients = {
    matchAll: vi.fn(),
    openWindow: vi.fn(),
  };
  const firebase = {
    initializeApp: () => {},
    messaging: () => ({}),
  };
  new Function("importScripts", "firebase", "self", "clients", source)(
    () => {},
    firebase,
    self,
    clients
  );
  if (!handler) throw new Error("notificationclick handler was not registered");
  return { handler, clients };
};

const click = async (
  handler: (event: unknown) => void,
  link: string | undefined
) => {
  const pending: Promise<unknown>[] = [];
  handler({
    notification: {
      close: vi.fn(),
      data: { FCM_MSG: { data: link ? { link } : {} } },
    },
    waitUntil: (promise: Promise<unknown>) => pending.push(promise),
  });
  await Promise.all(pending);
};

const windowClient = () => ({ focus: vi.fn(), postMessage: vi.fn() });

describe("firebase-messaging-sw notificationclick", () => {
  it("focuses an open window when the push has no link", async () => {
    const { handler, clients } = loadHandler();
    const client = windowClient();
    clients.matchAll.mockResolvedValue([client]);

    await click(handler, undefined);

    expect(client.focus).toHaveBeenCalled();
    expect(client.postMessage).not.toHaveBeenCalled();
    expect(clients.openWindow).not.toHaveBeenCalled();
  });

  it("opens the app when there is no window and no link", async () => {
    const { handler, clients } = loadHandler();
    clients.matchAll.mockResolvedValue([]);

    await click(handler, undefined);

    expect(clients.openWindow).toHaveBeenCalledWith(SCOPE);
  });

  it("posts the link to an open window", async () => {
    const { handler, clients } = loadHandler();
    const client = windowClient();
    clients.matchAll.mockResolvedValue([client]);

    await click(handler, LINK);

    expect(client.postMessage).toHaveBeenCalledWith({
      type: "NOTIFICATION_CLICK",
      link: LINK,
    });
    expect(client.focus).toHaveBeenCalled();
  });

  it("opens the link when there is no window", async () => {
    const { handler, clients } = loadHandler();
    clients.matchAll.mockResolvedValue([]);

    await click(handler, LINK);

    expect(clients.openWindow).toHaveBeenCalledWith(LINK);
  });
});
