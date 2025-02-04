import { ApplicationInsights } from '@microsoft/applicationinsights-web';
import { ReactPlugin } from '@microsoft/applicationinsights-react-js';

class TelemetryService {
    private static instance: TelemetryService;
    private appInsights: ApplicationInsights;

    private constructor() {
        const reactPlugin = new ReactPlugin();
        this.appInsights = new ApplicationInsights({
            config: {
                connectionString: 'InstrumentationKey=9b874779-5534-4383-b554-e5b2c4e44827;IngestionEndpoint=https://westeurope-5.in.applicationinsights.azure.com/;LiveEndpoint=https://westeurope.livediagnostics.monitor.azure.com/;ApplicationId=d9a282d1-a902-4603-beff-b021880dca79',
                enableAutoRouteTracking: true,
                extensions: [reactPlugin],
            }
        });
        this.appInsights.loadAppInsights();
    }

    public static getInstance(): TelemetryService {
        if (!TelemetryService.instance) {
            TelemetryService.instance = new TelemetryService();
        }
        return TelemetryService.instance;
    }

    public logError(error: Error): void {
        this.appInsights.trackException({ exception: error });
    }
}

const telemetryService = TelemetryService.getInstance();

export { telemetryService };