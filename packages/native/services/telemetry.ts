class TelemetryService {
    private static instance: TelemetryService;

    private constructor() { }

    public static getInstance(): TelemetryService {
        if (!TelemetryService.instance) {
            TelemetryService.instance = new TelemetryService();
        }
        return TelemetryService.instance;
    }

    public logInfo(eventName: string, eventData?: unknown): void {
        console.log(`Info: ${eventName}`, eventData);
    }

    public logError(errorName: string, errorData?: unknown): void {
        console.error(`Error: ${errorName}`, errorData);
    }
}

const telemetry = TelemetryService.getInstance();

export { telemetry };