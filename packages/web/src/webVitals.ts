import { trace } from "@opentelemetry/api";
import {
  onCLS,
  onFCP,
  onINP,
  onLCP,
  onTTFB,
  type Metric,
} from "web-vitals";
import { isNativePlatform } from "./utils/platform";

export const WEB_VITAL_SPAN_PREFIX = "web_vital.";
export const APP_LAUNCH_SPAN_NAME = "app_launch";

const tracer = trace.getTracer("web-vitals");

const platform = () => (isNativePlatform() ? "native" : "web");

const recordMetric = (metric: Metric) => {
  const now = Date.now();
  const span = tracer.startSpan(`${WEB_VITAL_SPAN_PREFIX}${metric.name}`, {
    startTime: now,
    attributes: {
      "web_vital.name": metric.name,
      "web_vital.value": metric.value,
      "web_vital.delta": metric.delta,
      "web_vital.rating": metric.rating,
      "web_vital.navigation_type": metric.navigationType,
      "web_vital.id": metric.id,
      "app.platform": platform(),
    },
  });
  span.end(now);
};

export function reportWebVitals() {
  onLCP(recordMetric);
  onINP(recordMetric);
  onCLS(recordMetric);
  onFCP(recordMetric);
  onTTFB(recordMetric);
}

let launchReported = false;

export function reportAppLaunch() {
  if (launchReported || !isNativePlatform()) return;
  launchReported = true;

  const duration = performance.now();
  const end = Date.now();
  const span = tracer.startSpan(APP_LAUNCH_SPAN_NAME, {
    startTime: end - duration,
    attributes: {
      "app.launch.duration_ms": duration,
      "app.platform": platform(),
    },
  });
  span.end(end);
}
