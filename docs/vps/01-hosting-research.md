# Hosting provider research

Checked on 7 November 2026. All prices are monthly and exclude VAT; an Irish customer without a VAT number adds 23%.

## Recommendation

Do not commit to Hetzner yet. The CX33 and CX23 the design is priced on have shown as unorderable on Hetzner's site since at least September 2026 and were still unavailable on 7 November 2026, and Hetzner's x86 types that might be orderable instead (CPX32 and CPX12, about €48) lose most of the saving. If the Cloud Console offers a CX33 when the staging box is built, stay with Hetzner; otherwise switch to Scaleway (DEV1-L and DEV1-S, about €42 plus block storage), the cheapest checked option found to meet every dependency without design changes, or to UpCloud Starter (about €26) if a stateless firewall with explicit return-traffic rules is acceptable. None of the managed platforms comes in under Railway's $68.

## Comparison

Production is 4 vCPU and 8 GB, or the nearest size. Staging is the smallest size with at least 2 GB of memory, since Django, the worker and Postgres share it. "Stateful" means replies to the box's own outbound connections are let back in without inbound rules, which is what lets cloudflared work behind a firewall with no inbound rules.

| Provider | Production | Staging | Firewall outside the host | Console | x86 | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Hetzner, as designed | CX33 €8.99 | CX23 €5.99 | Yes, stateful, no rules means inbound dropped | Yes | Yes | €14.98 total. Not orderable on the public site on 7 Nov 2026. EU only. |
| Hetzner, CPX fallback | CPX32 €35.99 | CPX12 €11.99 | Same | Yes | Yes (AMD) | €47.98 total. The public site also showed CPX as unavailable on 7 Nov 2026. |
| Hetzner, US | CPX31 €62.99 | CPX11 €17.99 | Same | Yes | Yes | €80.98 total. No CX types in Ashburn or Hillsboro. |
| OVHcloud VPS | VPS-2 $8.50 | VPS-1 $4.54 | Partly: Edge Network Firewall is stateless and IPv4 only | Yes (KVM) | Yes | $13.04 "from" prices on the US site. cloud-init on VPS not confirmed. |
| Scaleway | DEV1-L €30 + IPv4 €2.92 | DEV1-S €6 + IPv4 €2.92 | Yes, stateful security groups with a default inbound policy | Yes (not re-checked) | Yes | €41.84 plus block storage, whose price could not be confirmed. Prices rose on 1 June 2026. |
| DigitalOcean | $48 | $12 (1 vCPU, 2 GB) | Yes, stateful | Yes | Yes | $60 total. IPv4 included. |
| Vultr | Regular $40, High Performance $48 | $10 or $12 | Yes | Yes | Yes | $50 to $60 total. IPv4 inclusion not stated on the pricing page. |
| Akamai/Linode | $48 | $12 | Yes | Yes (Lish/Glish) | Yes | $60 total. Some regions cost more. |
| UpCloud | Starter 4 vCPU 8 GB €20 | Starter 1 vCPU 2 GB €6 | Partly: free, but stateless | Yes | Yes | €26 total. 40 GB disk on the 8 GB Starter. Starter uses previous-generation hardware. |
| netcup | VPS 1000 G12.5 €14.50 | VPS 500 G12.5 €8.26 | Partly: stateful for TCP only, no API mentioned | Yes | Yes | €22.76 on 12-month terms. Servers are ordered by hand, not through an API. |
| Contabo | Cloud VPS 10 €4.50 | Cloud VPS 10 €4.50 | Partly: default drop, panel only, enforcement point not stated | Yes (VNC) | Yes | €9.00 total. Pricing page undated; confirm setup fees and current price before relying on it. |

## Question 1: Is Hetzner still the best value?

On list price, yes for the EU, but the list price cannot currently be bought.

**Prices.** Hetzner raised cloud prices twice in 2026: a broad rise announced on 23 February and effective 1 April, and a second round effective 15 June 2026 for new orders and rescales ([heise](https://heise.de/-11333037), [Capital & Compute, secondary](https://capitalandcompute.net/md/hetzner-price-increase-2026.md)). The 15 June table raised the CX33 from €6.49 to €8.49 and the CX23 from €3.99 to €5.49 in Germany and Finland, while the CPX line more than doubled, for example CPX32 from €13.99 to €35.49 ([Hetzner price adjustment](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/), checked 7 Nov 2026). A Primary IPv4 costs €0.50 ([Hetzner IPv4 pricing](https://docs.hetzner.com/general/infrastructure-and-availability/ipv4-pricing), checked 7 Nov 2026), which the product pages now include: CX33 €8.99 and CX23 €5.99 ([Cost-Optimized page](https://www.hetzner.com/cloud/cost-optimized/), checked 7 Nov 2026). The design's two boxes come to €14.98, or €18.43 with Irish VAT.

**Orderability.** On 7 November 2026 every Cost-Optimized type (CX23 to CX53 and CAX11 to CAX41) carried "currently unavailable, please check back later", and the page says the line runs on older hardware in limited numbers ([Cost-Optimized page](https://www.hetzner.com/cloud/cost-optimized/)). Third-party checks found the same on 2 September, 8 September, 13 October and 20 October 2026 ([StackValueLab](https://stackvaluelab.com/hetzner-cx-cax-unavailable/), [bitdoze](https://www.bitdoze.com/es/hetzner-cloud-precios-2026/), both secondary). One report says API creates of cx23 and cx33 succeeded on 19 September 2026 while the site showed them unavailable, and later failed with `resource_unavailable` ([agentdeals issue #2960](https://github.com/robhunter/agentdeals/issues/2960), secondary). The Regular Performance page showed every CPX type as unavailable too on 7 November 2026 ([Regular Performance page](https://www.hetzner.com/cloud/regular-performance)); this was read from the public page and may not match what a Cloud Console project is offered. The Cloud Console order screen is the only authoritative check, and it was not used because no account was created. A report cites a Hetzner status notice, up since 26 June 2026, that cloud servers can only be provisioned to a limited extent ([privatedevops](https://privatedevops.com/news/hetzner-cpx02-1gb-cloud-server), secondary); the notice itself was not found.

**Locations.** CX and CAX exist only in Falkenstein, Nuremberg and Helsinki. The US locations offer only the older CPX11 to CPX51 and CCX types ([Hetzner price adjustment](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)).

**Account verification.** Hetzner may ask for a government ID or a credit-card prepayment, and may reject or hold sign-ups that use a free email address or a VPN, or first orders it finds implausible; queries go to cda-review@hetzner.com, with no formal appeal described ([Fraud prevention FAQ](https://docs.hetzner.com/general/security-and-identify/fraud-prevention-faq/), checked 7 Nov 2026). Reports of refused accounts are common on forums but were not counted here. No primary source on abuse-driven suspensions was found.

**Reliability.** Status-page mirrors show cloud network leaf faults in Nuremberg and a Hillsboro leaf (hil-cloud1-leaf8) with limited connectivity from 11 to 13 September 2026, about 40 hours ([pulsetic mirror of Hetzner status](https://pulsetic.com/status/hetzner/incidents/7162/), [isdown](https://isdown.app/status/hetzner/incidents/630664-cloud-leaf-fault-nbg1-cloud1-leaf97), both secondary). A single leaf fault takes down only the servers behind that switch, but a single box has no failover.

**Dependencies.** Hetzner meets all of them: x86 CX and CPX types, a stateful Cloud Firewall where no inbound rules means all inbound is dropped ([Firewall FAQ](https://docs.hetzner.com/cloud/firewalls/faq/), checked 7 Nov 2026), a web console, and the API and `hcloud` CLI with cloud-init user data.

## Question 2: Other VPS providers

All prices checked on 7 November 2026 unless noted.

- **OVHcloud.** VPS-2 (4 vCores, 8 GB, 75 GB NVMe) from $8.50 and VPS-1 (2 vCores, 4 GB, 40 GB) from $4.54, with unlimited traffic, daily backups, a KVM console and an API ([OVHcloud US VPS page](https://us.ovhcloud.com/vps/)). These are "from" prices and the commitment term behind them is not stated; EU prices were not confirmed. The Edge Network Firewall is stateless and IPv4 only, needs an explicit "TCP established" accept rule and a final deny rule, and allows 20 rules per IP ([OVHcloud Edge Network Firewall](https://docs.ovhcloud.com/en/guides/bare-metal-cloud/dedicated-servers/firewall-network)). IPv6 would have to be disabled or firewalled on the host. cloud-init user data on VPS was not confirmed.
- **Scaleway.** DEV1-L (4 vCPU, 8 GB, AMD EPYC 7281) about €30 and DEV1-S (2 vCPU, 2 GB) about €6; a flexible IPv4 is €0.004 an hour, about €2.92 a month ([Scaleway Instances pricing](https://www.scaleway.com/en/pricing/virtual-instances/)). PLAY2-MICRO (4 vCPU, 8 GB) is about €39. Scaleway raised DEV1, PLAY2 and PRO2 prices on 1 June 2026 ([Scaleway pricing update](https://www.scaleway.com/en/blog/a-transparent-update-on-scaleway-pricing/)). Block storage price could not be confirmed. Security groups can be stateful with configurable default policies, and instances take cloud-init ([Instances concepts](https://www.scaleway.com/en/docs/instances/concepts/)); the console and `scw` CLI cover servers and security groups ([scw instance](https://cli.scaleway.com/instance/)).
- **DigitalOcean.** Basic 4 vCPU, 8 GB, 160 GB, 5 TB transfer for $48; 1 vCPU, 2 GB for $12; IPv4 included; per-second billing from 1 January 2026 ([Droplet pricing](https://www.digitalocean.com/pricing/droplets)). Cloud Firewalls are free and stateful, managed by API and `doctl` ([Firewalls](https://docs.digitalocean.com/products/networking/firewalls/details/features/)). Meets every dependency.
- **Vultr.** Regular Performance 4 vCPU, 8 GB for $40; High Performance AMD or Intel 4 vCPU, 8 GB, NVMe for $48 ([Vultr pricing](https://www.vultr.com/pricing/)). Firewall groups are free ([Firewall groups](https://docs.vultr.com/products/network/firewall-groups)). Regular Performance uses previous-generation Intel CPUs. Whether IPv4 is included was not stated on the pricing page.
- **Akamai/Linode.** Linode 8 GB (4 vCPU) $48, Linode 2 GB $12, overage $0.005/GB ([Akamai CPU pricing](https://www.akamai.com/cloud/pricing/cpu)). The page says some regions cost more without listing them. Cloud Firewalls are free with a selectable default inbound policy ([Cloud Firewalls](https://techdocs.akamai.com/cloud-computing/docs/cloud-firewall)).
- **UpCloud.** Starter 4 vCPU, 8 GB, 40 GB for €20 and 1 vCPU, 2 GB, 20 GB for €6; one IPv4 included; firewall €0; zero-cost egress under a fair transfer policy ([UpCloud pricing](https://upcloud.com/pricing/)). The page says price changes take effect on 16 November, which suggests these Starter prices apply from that date. Starter was introduced on 15 April 2026 on previous-generation hardware, aimed at development, staging and small web apps ([Starter and Premium changelog](https://upcloud.com/docs/changelog/2026-04-15-starter-premium-servers/)). The firewall is stateless: a Drop default works, but return traffic for cloudflared, DNS and NTP needs explicit inbound rules for both IPv4 and IPv6 ([UpCloud firewall guide](https://upcloud.com/docs/guides/managing-firewall/)). Firewall rules have an API ([API: Firewall](https://developers.upcloud.com/1.2/11-firewall/)). Zones offering Starter were not confirmed.
- **netcup.** VPS 1000 G12.5 (4 vCores, 8 GB, 128 GB) €14.50 and VPS 500 G12.5 (2 vCores, 4 GB, 64 GB) €8.26, both on 12-month terms; locations include Nuremberg, Vienna, Amsterdam and Manassas in the US ([netcup VPS](https://www.netcup.com/en/server/vps)). The firewall is free, upstream and stateful for TCP but not UDP, and is managed in the Server Control Panel; no API is mentioned ([netcup firewall](https://www.netcup.com/en/helpcenter/documentation/server/firewall)). Servers are bought through the shop rather than created by API, so the cloud-init provisioning flow does not carry over.
- **Contabo.** Cloud VPS 10 (4 vCPU, 8 GB, 75 GB NVMe, 200 Mbit/s) for €4.50 ([Contabo pricing](https://contabo.com/en-us/pricing/)); the page is undated and setup fees and term pricing were not shown. The free firewall drops unsolicited inbound by default and is managed in the Customer Panel; the article does not say where it is enforced, whether it is stateful, or whether it has an API ([Contabo firewall](https://help.contabo.com/en/support/solutions/articles/103000390430-firewall-what-is-it-and-how-does-it-protect-my-vps-vds-)). The 200 Mbit/s port is enough for 50 GB a month.

## Question 3: Managed platforms

Sizing used for every platform: two web instances of about 1 vCPU and 2 GB, a small worker, and Postgres with 2 to 4 GB of memory and 10 to 15 GB of storage; staging at the smallest paid sizes. Prices in USD, checked 7 November 2026.

| Option | Monthly total | Config in repo | Off-site WAL and PITR | Restore drill | Overlapping deploys, migrations first | Real client IPs |
| --- | --- | --- | --- | --- | --- | --- |
| Render (Hobby) | about $145 | Yes, `render.yaml` | Partly: PITR 3 days on Hobby, 7 on Pro, held by Render | Yes, restore to a new instance | Yes | Partly: `X-Forwarded-For` |
| Fly.io + Fly Managed Postgres | about $199 | Partly: `fly.toml`; MPG created by CLI | Partly: PITR, 10-day backups, held by Fly | Yes, `fly mpg restore` to a new cluster | Yes | Yes, `Fly-Client-IP` |
| Fly.io + Neon (Launch) | about $130 to $169 | Partly | Partly: up to 7-day history, held by Neon | Yes, branch at a timestamp | Yes | Yes |
| Koyeb + Koyeb Postgres | about $175 | Partly | Not confirmed | Not confirmed | Partly | Not confirmed |
| Northflank | about $127 | Partly, templates | Not confirmed: "backups and restores" listed | Not confirmed | Partly | Not confirmed |
| Supabase, database only | about $175 for production Postgres alone | n/a | Partly: PITR add-on | Yes | n/a | n/a |
| Crunchy Bridge, database only | about $81 for both databases | n/a | Partly: PITR included | Yes | n/a | n/a |

"Partly" in the WAL column means the archive is held by the same company that runs the database, so losing the account loses both the database and its backups. The design keeps WAL in Cloudflare R2, outside the provider. Every managed option below still needs a separate scheduled `pg_dump` off the platform to match that.

How the totals were built:

- **Render.** Web 2 × 1 CPU 2 GB at $25, worker 512 MB at $7, Postgres 1 CPU 4 GB at $55, storage 15 GB at $0.30; staging web and worker at $7 each and Postgres 256 MB at $6 plus 5 GB; 45 GB bandwidth overage at $0.15 on Hobby ([Render pricing](https://render.com/pricing)). The Pro workspace adds $25. Render keeps the old instance serving until the new one passes its checks, runs a pre-deploy command for migrations, and applies this to background workers ([zero-downtime deploys](https://render.com/articles/how-render-handles-zero-downtime-deploys)). PITR restores to a new instance; logical exports are kept 7 days; WAL cannot be sent to your own bucket ([Render Postgres backups](https://render.com/docs/postgresql-backups)). Render appends its proxy address to `X-Forwarded-For`, so Django has to trust exactly the right number of hops, which with Cloudflare in front is two ([Render community, secondary](https://community.render.com/t/accessing-client-ips-in-a-node-express-app/36282)).
- **Fly.io.** Compute prices are for Ashburn; Amsterdam is 1.038 times that ([Fly pricing](https://fly.io/pricing.md)). Shared CPUs are only suited to bursty load, so web uses 2 × performance-1x 2 GB ($33 each before the multiplier). Worker shared-cpu-2x 512 MB $4.39. Managed Postgres Starter (shared-2x, 2 GB) $72 and Basic (1 GB) $38 for staging, storage $0.28/GB, egress $0.02/GB in Europe and North America ([Fly pricing](https://fly.io/pricing/), [Managed Postgres](https://fly.io/mpg/)). Managed Postgres supports point-in-time restore into a new cluster and keeps backups 10 days; clusters cannot be upgraded across Postgres major versions in place ([Fly Postgres docs](https://docs.fly.io/postgres)). Running staging Postgres on an ordinary Fly machine with a volume instead of Managed Postgres brings the total to about $163, assuming a $5 machine and volume.
- **Neon.** Launch plan: $0.106 per compute-unit hour, $0.35/GB-month storage, history up to 7 days at $0.20/GB-month, 500 GB egress included ([Neon pricing](https://neon.com/pricing), page last updated 4 Nov 2026). Five-second polling keeps production compute awake all month: 1 CU (4 GB) is about $77, 0.5 CU about $39. The history-storage figure assumes about 10 GB of WAL, which is a guess. The database would sit in an AWS region, so every Django query from Fly crosses networks; that latency was not measured.
- **Koyeb.** Pro plan $29 including $10 of compute; eco-large (2 vCPU, 4 GB) $21.43, eco-small $5.36; Postgres Medium (0.5 vCPU, 2 GB) $59.52 and Small $29.76, storage $0.50/GB; 1 TB bandwidth included on Pro ([Koyeb pricing](https://www.koyeb.com/pricing), [instance types](https://www.koyeb.com/docs/reference/instances)). Whether Koyeb Postgres offers PITR was not confirmed. The pricing page carries a banner that Koyeb is joining Mistral AI.
- **Northflank.** 1 vCPU 2 GB $24, 0.5 vCPU 1 GB $12, Postgres 0.5 vCPU 1 GB with 10 GB about $13.17, disk $0.117/GiB, egress $0.06/GB ([Northflank pricing](https://northflank.com/pricing)). PITR is not mentioned. Northflank disclosed a breach on 30 October 2026 and told customers to assume all environment variables had been decrypted ([BleepingComputer](https://bleepingcomputer.com/news/security/northflank-security-breach-leads-to-abuse-of-customers-ai-api-keys)); the same report lists Railway among platforms hit in the same wave.
- **Supabase.** Pro $25 with $10 compute credit, Medium compute about $60, PITR add-on about $100 a month for 7 days ([compute](https://supabase.com/docs/guides/platform/manage-your-usage/compute), [PITR](https://supabase.com/docs/guides/platform/manage-your-usage/point-in-time-recovery)). Too expensive for this database size.
- **Crunchy Bridge.** Standard-4 (1 core, 4 GB) $70 plus storage, Hobby-0 $9 for staging, PITR included, from a secondary summary dated 27 October 2026 ([CostBench, secondary](https://costbench.com/software/database-as-service/crunchy-bridge/)). Not confirmed from Crunchy's own page. It would still need an app platform, so the total exceeds Railway.

None of these meets all five conditions for less than Railway's $68, and none keeps the WAL archive outside the provider. The VPS plan remains the only option that meets the original conditions at a lower cost.

## Question 4: A box closer to North America

Users connect to Cloudflare's nearest location, and the tunnel carries requests from there to the origin, so moving the box only changes the Cloudflare-to-origin leg. With most users in Europe and North America, an origin in western Europe costs North American users one transatlantic round trip per uncached request, and the reverse holds for a US origin. For an app that mostly answers 5-second polls with 304s, that is noticeable but not limiting.

At Hetzner a US box is far worse: there are no CX types in Ashburn or Hillsboro, and the closest match to the CX33, the CPX31, is €62.99 against €8.99 for the CX33, with 3 TB of traffic instead of 20 TB ([Regular Performance page](https://www.hetzner.com/cloud/regular-performance)). It is not easier to order either, since the public page showed it as unavailable on 7 November 2026. DigitalOcean, Vultr and UpCloud list one price across regions, Linode charges more in some regions, OVHcloud and netcup offer US locations (Manassas for netcup), and Fly.io charges 1.000 in Ashburn against 1.038 in Amsterdam. If a US origin matters, it is a reason to leave Hetzner, not to change Hetzner location.

## What each serious alternative changes in the design

### Hetzner CPX instead of CX

No change beyond the type names in the provisioning scripts. Cost rises to about €48, and orderability still has to be confirmed in the Console. CPX02 (1 GB) is too small for staging with Postgres on it.

### Scaleway

- Replace `hcloud` with `scw` and the Hetzner firewall with a stateful security group whose inbound default is drop, with no inbound rules.
- Choose DEV1 or PLAY2 types and check whether they boot from block storage, then add its cost.
- A flexible IPv4 is billed separately; IPv6-only would need checking against cloudflared and package mirrors.
- Locations: Paris, Amsterdam and Warsaw. No North American region.

### UpCloud

- Replace `hcloud` with `upctl` or the API.
- The firewall is stateless, so "no inbound rules" becomes a short set of inbound accepts for replies: TCP from Cloudflare's tunnel ports, DNS from the resolvers, NTP, and package mirrors, each for IPv4 and IPv6. These live in the repo alongside the server definition. The check script should test that nothing else is reachable.
- The Starter disk is 40 GB, half of the design's 80 GB. With a 4.4 GB database and WAL shipped to R2 this fits, but Docker image pruning matters more.
- Starter is described as previous-generation hardware for development and small apps; confirm it suits production before use, or price a Premium plan (4 vCPU, 8 GB for €52).

### DigitalOcean, Vultr or Linode

- Replace `hcloud` with `doctl`, `vultr-cli` or `linode-cli`; all three have free cloud firewalls, consoles and cloud-init.
- Cost is about $50 to $60, close to Railway's $68, so the move's main gain becomes control over backups and deploys rather than cost.
- All three offer North American and European regions at the same or similar price.

### OVHcloud VPS

- Cheapest checked option that has an API and console, but its firewall is stateless and covers IPv4 only, so the design would need host-level filtering for IPv6 and a "TCP established" rule, and cloud-init support would have to be confirmed.
- Daily backups are included even though the design does not need them.

## Figures not confirmed from a primary source

- Hetzner orderability through the Cloud Console and API, and Hetzner's 26 June 2026 capacity notice.
- Scaleway block storage price and whether DEV1 types boot from block storage; Scaleway serial console was not re-checked.
- OVHcloud EU prices, commitment terms behind the "from" prices, and cloud-init on VPS.
- Vultr IPv4 inclusion; Linode regional surcharges.
- UpCloud zones for Starter plans, and whether the €20 and €6 Starter prices apply before 16 November 2026.
- Contabo setup fees and the date of its prices.
- Crunchy Bridge prices (secondary source only).
- Koyeb and Northflank Postgres point-in-time recovery.
- Render's client IP behaviour (community thread only).
- Neon history storage for this workload (estimated).
