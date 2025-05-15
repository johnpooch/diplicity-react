class DevelopmentTelemetryService {
    private static instance: DevelopmentTelemetryService;

    private constructor() { }

    public static getInstance(): DevelopmentTelemetryService {
        if (!DevelopmentTelemetryService.instance) {
            DevelopmentTelemetryService.instance = new DevelopmentTelemetryService();
        }
        return DevelopmentTelemetryService.instance;
    }

    public logInfo(message: string): void {
        console.info('Telemetry Info:', message);
    }

    public logError(error: Error): void {
        console.error('Telemetry Error:', error);
    }
}

export { DevelopmentTelemetryService };