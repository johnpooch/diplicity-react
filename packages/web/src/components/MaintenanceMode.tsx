export function MaintenanceMode() {
  return (
    <div className="max-w-sm mx-auto">
      <div className="flex flex-col items-center justify-center min-h-screen text-center gap-6">
        <h1 className="text-2xl font-bold">Maintenance Mode</h1>
        <p className="text-muted-foreground">
          We're currently performing scheduled maintenance to improve the
          experience. Please check back in a few minutes.
        </p>
      </div>
    </div>
  );
}
