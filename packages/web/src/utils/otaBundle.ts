import * as Sentry from "@sentry/react";
import { CapacitorUpdater } from "@capgo/capacitor-updater";
import { setNativeVersions } from "../observability";

const reportOtaBundle = async (): Promise<void> => {
  try {
    const { bundle, native } = await CapacitorUpdater.current();
    setNativeVersions({ otaBundle: bundle.version, nativeBinary: native });
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
