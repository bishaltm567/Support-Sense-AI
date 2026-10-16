# SupportSense AI — cost and usage report

## Scope and status

This repository contains a local-only default implementation and optional Databricks integrations. No Databricks usage or billing data is available in this environment; cloud cost is **unknown / not measured**, not zero. Local app execution has no model inference charge; electricity, device, and network costs are not measured.

## Record actuals before presenting

| Component | Measurement period | Usage source | Actual usage | Actual cost | Status |
|---|---|---|---:|---:|---|
| Databricks compute | Not measured | Workspace usage/billing UI | — | Unknown | Requires workspace |
| Model Serving inference | Not measured | Serving endpoint usage/billing | — | Unknown | Endpoint not configured |
| Embeddings / Vector Search | Not used in local baseline | Endpoint/index billing | — | Not applicable locally | Optional service |
| Delta storage | Not measured | Cloud storage / billing | — | Unknown | Requires cloud deployment |
| Local development | This workstation | No metering available | — | Unknown | Not billed by this app |

## Methodology

1. Record the workspace billing period, cloud provider, region, SKU, and currency.
2. Export actual DBU/compute, serving tokens/requests, vector index, and storage charges from the workspace billing and cloud billing sources.
3. Attribute shared resources explicitly; do not assign all shared compute to this demo.
4. Label projected spend as an estimate and state the rate card/date used.
5. Keep measured costs distinct from local execution and free-tier/trial entitlements. A free or trial entitlement does not prove that all workloads incur zero charges.

## Free-tier and trial notes

Workspace features and included quotas change. Verify availability and limits in the actual workspace before enabling compute, model serving, Vector Search, or storage. Stop/delete billable resources after the demo according to workspace policy.
