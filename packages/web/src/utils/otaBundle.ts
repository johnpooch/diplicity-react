import * as Sentry from "@sentry/react";
import { CapacitorUpdater } from "@capgo/capacitor-updater";

const reportOtaBundle = async (): Promise<void> => {
  try {
    const { bundle } = await CapacitorUpdater.current();
    Sentry.setTag("ota_bundle", bundle.version);

    const failed = await CapacitorUpdater.getFailedUpdate();
    if (failed) {
      Sentry.captureMessage(
        `OTA bundle ${failed.bundle.version} was rolled back`,
        "warning"
      );
    }
  } catch (error) {
    console.error("Failed to report the OTA bundle:", error);
  }
};

export { reportOtaBundle };
