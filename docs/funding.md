# Getting dedicated hardware

Free GitHub runners are shared VMs. They are fine for correctness, plan changes, CPU time
and input bytes, but wall-time differences below roughly 10% are mostly noise. Comparable
numbers over months need the *same* dedicated machine (or cluster) for every run. This page
lists who might provide it and what to ask for. Checked November 2026.

## What to ask for

| profile | hardware | monthly cost at list prices (rough order of magnitude) |
|---|---|---|
| `large-vm` | one dedicated 32 vCPU / 128 GB VM, 500 GB NVMe | a few hundred USD on demand, much less with a dedicated or reserved host |
| `k8s-4-workers` | 5 nodes x 16 vCPU / 64 GB, S3 bucket, Iceberg REST catalog | roughly 1-2k USD if always on; far less if nodes are created per run |

Both are registered as self-hosted GitHub runners (`runner:` in the profile). Only
maintainer-started workflows (form, approved issues, schedules) run on them; pull requests
from forks never do.

## Candidates

**Cloud open-source credit programs**

- **AWS Open Source Promotional Credits.** Still active: AWS reaffirmed the program in 2025
  ([AWS blog](https://aws.amazon.com/fr/blogs/opensource/aws-cloud-credits-for-open-source-projects-affirming-our-commitment/)),
  and OpenSSF described it in September 2026
  ([OpenSSF](https://openssf.org/blog/2026/09/14/empowering-open-source-security-with-scalable-infrastructure/)).
  AWS also has a direct interest: Amazon Athena engine version 3 is built on Trino.
- **Google Cloud credits for open source.** Program terms are published
  ([Google Cloud](https://cloud.google.com/terms/open-source-software-tos)).
- **Microsoft Azure.** The [Azure credits page](https://opensource.microsoft.com/azure-credits/)
  is still online, but Microsoft reportedly discontinued Azure Sponsored Subscriptions for
  open-source maintainers in September 2025 and now sponsors only strategic projects
  ([summary](https://www.eliostruyf.com/whos-funding-open-source-2025-guide-maintainers/)).
  Low priority.
- **Oracle Cloud.** The Always Free tier includes Ampere A1 Arm capacity (4 OCPU / 24 GB),
  enough for the `oci-a1-arm` profile at no cost. Oracle has also run an
  [Arm Accelerator](https://go.oracle.com/armaccelerator-welcome) credit program and gave
  CNCF $3M a year in Arm credits
  ([Oracle](https://www.oracle.com/news/announcement/oracle-expands-support-for-open-source-community-2023-11-07/)).
  This is the quickest way to get a dedicated, unshared machine. Trino publishes arm64 images.

**Companies whose products depend on Trino or Iceberg performance**

- **Starburst** contributes the majority of Trino's core development
  ([Starburst](https://www.starburst.io/trino/)) and benchmarks Trino internally; public,
  reproducible numbers for every release and PR are directly useful to them.
- **AWS** (Athena, EMR), and large Trino users that run it at scale, such as Netflix, LinkedIn
  and Lyft.
- **Iceberg catalog and storage vendors** (Snowflake/Polaris, Databricks/Tabular, Dremio,
  Cloudera). The cross-engine comparison on the same Iceberg tables is the part they care about.
- **Hardware vendors** that want Trino numbers on their CPUs: Ampere and Arm (Arm servers),
  AMD and Intel (x86), NVIDIA (Starburst announced a GPU engine based on Trino in October 2026).

**Foundations**

- The **Trino Software Foundation** holds the project; a benchmark service that the Trino
  maintainers find useful is the strongest argument for any sponsor.

## Gone or not a fit

- **Equinix Metal** shut down in June 2026, ending its free bare metal for open-source projects
  ([FOSS Force](https://fossforce.com/2026/01/alpine-linux-turns-equinix-metal-exit-into-an-infrastructure-upgrade/)).
- **CNCF Community Infrastructure Lab** served CNCF projects and is described as past
  ([cncf/cluster](https://github.com/cncf/cluster)); Trino is not a CNCF project.
- **GitHub larger runners** are billed even for public repositories
  ([WarpBuild](https://www.warpbuild.com/answers/are-github-actions-free-for-open-source)).

## Suggested order

1. Register an Oracle Cloud Always Free Ampere A1 VM as a runner and enable `oci-a1-arm`
   (free, dedicated, available now).
2. With a few weeks of published release and PR results, apply for AWS open-source credits
   and approach Starburst for the `large-vm` profile.
3. Ask the Trino maintainers whether they want PR benchmarks from this service, then go for
   the `k8s-4-workers` cluster.
