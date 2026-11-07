# Railway resource metrics in Honeycomb

The existing Procrastinate worker exports Railway resource metrics every minute.
It queries Railway's GraphQL API and sends OTLP metrics directly to Honeycomb.
There is no additional service, collector, public endpoint, or Railway cron job.

## Enable the export

After deploying the migration and updated worker, set these variables on the
worker service only:

| Variable | Value |
| --- | --- |
| `RAILWAY_METRICS_API_TOKEN` | A Railway account or workspace API token with access to the project. This is an explicit opt-in, separate from deployment credentials. |
| `HONEYCOMB_API_KEY` | A Honeycomb ingestion key with permission to write metrics. The existing tracing key can be reused if it has this permission. |
| `HONEYCOMB_METRICS_ENDPOINT` | Optional. Defaults to `https://api.honeycomb.io:443`; use `https://api.eu1.honeycomb.io:443` for an EU Honeycomb team. |

Railway supplies `RAILWAY_ENVIRONMENT_ID` automatically. All three required
values (the two keys and environment ID) must be present before the task queries
Railway or writes a checkpoint. Missing configuration disables the export.
Use sealed variables for the keys so they are not copied into preview environments.
Account and workspace tokens can perform writes too; do not treat them as
read-only credentials. The exporter only makes GraphQL queries.

The existing worker start command is unchanged:

```sh
python manage.py procrastinate worker
```

Honeycomb's current metrics experience routes OTLP metrics into its managed
`Metrics` dataset. The exporter does not set a dataset header or change application
tracing configuration.

## Measurements and labels

| Honeycomb metric | Railway measurement | Unit |
| --- | --- | --- |
| `railway.cpu.usage` | `CPU_USAGE` | vCPU |
| `railway.cpu.limit` | `CPU_LIMIT` | vCPU |
| `railway.memory.usage` | `MEMORY_USAGE_GB` | GiB |
| `railway.memory.limit` | `MEMORY_LIMIT_GB` | GiB |
| `railway.disk.usage` | `DISK_USAGE_GB` | GiB |
| `railway.ephemeral_disk.usage` | `EPHEMERAL_DISK_USAGE_GB` | GiB |
| `railway.backup.usage` | `BACKUP_USAGE_GB` | GiB |
| `railway.network.ingress` | `NETWORK_RX_GB` | GiB |
| `railway.network.egress` | `NETWORK_TX_GB` | GiB |

Values are exported as gauges with Railway's original timestamps and values,
including zeroes. Network values retain Railway's representation; they are not
converted into cumulative counters, rates, or estimated charges. Check their
aggregation against Railway's usage reporting before calculating a bill.

Every series includes `service.name`, `deployment.environment`,
`railway.environment.id`, and `railway.service.id`. Resource series also include
deployment, instance, region, and volume identifiers when Railway supplies them.
Public network metrics are queried separately and grouped only by service,
because Railway does not provide per-replica public network traffic.

## Delivery and troubleshooting

The exporter requests one-minute samples, leaving a two-minute delay for Railway
to collect them. The first run fetches ten minutes. A database checkpoint records
the end of the last successfully delivered interval, so restarts resume from
there. Catch-up requests cover at most one hour per run. Empty intervals advance
without sending an empty batch. Samples belong to half-open intervals, so a
boundary timestamp is sent in the following interval rather than twice.

The Procrastinate task lock serializes exports. A failed Railway request, GraphQL
error, or rejected Honeycomb export logs a warning and leaves the checkpoint
unchanged for the next minute's run. Delivery is at least once: an acknowledged
export followed by a database failure can be resent. Samples arriving more than
two minutes late in Railway can be missed after their interval is checkpointed.

Look for `Exported ... Railway metric samples through ...` in worker logs, then
compare the corresponding service and time window in Honeycomb and Railway.
`Railway metrics export failed` means the next run will retry that interval.
There is no startup success message when configuration is missing.

Exporting depends on the worker and database being available. It does not provide
independent outage monitoring, and a missing feed is not evidence of zero usage.
Resource metrics and application traces remain separate: timestamps and labels
support comparison, not attribution of a platform bill to individual requests.
