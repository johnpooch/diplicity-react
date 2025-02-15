import { TelemetryService } from './telemetry.prod';
import { DevelopmentTelemetryService } from './telemetry.dev';
import { ITelemetryService } from './telemetry.types';

const telemetryService: ITelemetryService = process.env.NODE_ENV === 'production'
    ? TelemetryService.getInstance()
    : DevelopmentTelemetryService.getInstance();

export { telemetryService };