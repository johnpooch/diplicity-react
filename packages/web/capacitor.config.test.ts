import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import type { CapacitorConfig } from "@capacitor/cli";

const loadConfig = async (apiBaseUrl?: string): Promise<CapacitorConfig> => {
  vi.resetModules();
  if (apiBaseUrl === undefined) {
    delete process.env.VITE_DIPLICITY_API_BASE_URL;
  } else {
    process.env.VITE_DIPLICITY_API_BASE_URL = apiBaseUrl;
  }
  const module = await import("./capacitor.config");
  return module.default;
};

const updaterConfig = (config: CapacitorConfig) =>
  config.plugins?.CapacitorUpdater ?? {};

describe("CapacitorUpdater configuration", () => {
  const originalApiBaseUrl = process.env.VITE_DIPLICITY_API_BASE_URL;

  beforeEach(() => {
    delete process.env.VITE_DIPLICITY_API_BASE_URL;
  });

  afterEach(() => {
    if (originalApiBaseUrl === undefined) {
      delete process.env.VITE_DIPLICITY_API_BASE_URL;
    } else {
      process.env.VITE_DIPLICITY_API_BASE_URL = originalApiBaseUrl;
    }
  });

  it("points update checks at the configured API", async () => {
    const config = await loadConfig("https://api.example.com");
    expect(updaterConfig(config).updateUrl).toBe(
      "https://api.example.com/update/check/"
    );
  });

  it("tolerates a trailing slash on the API base url", async () => {
    const config = await loadConfig("https://api.example.com/");
    expect(updaterConfig(config).updateUrl).toBe(
      "https://api.example.com/update/check/"
    );
  });

  it("falls back to the local service when the API is not configured", async () => {
    const config = await loadConfig();
    expect(updaterConfig(config).updateUrl).toBe(
      "http://localhost:8000/update/check/"
    );
  });

  it("sends nothing to Capgo's servers", async () => {
    const config = await loadConfig("https://api.example.com");
    expect(updaterConfig(config).statsUrl).toBe("");
    expect(updaterConfig(config).channelUrl).toBe("");
  });

  it("applies downloaded bundles when the app next goes to background", async () => {
    const config = await loadConfig("https://api.example.com");
    expect(updaterConfig(config).autoUpdate).toBe("atBackground");
  });
});
