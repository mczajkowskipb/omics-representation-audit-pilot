# Reuse audit

Audited revisions:

- `rank-relational-clustering-feasibility`: `dc97680a1e944e74924b5e7b151e0c27d5655f22`
- `AIR-relational-benchmark`: `2dee739f6ee5e001ef1be76df2eb753ca389adb3`

The reference repositories remain unchanged and are not runtime dependencies.

## Reused concepts and assets

- per-sample rank representation and Footrule-distance concept;
- deterministic experiment-seed concept for later stages;
- feasibility datasets through future path-based adapters;
- AIR matrix/manifests through future path-based adapters;
- train-only preprocessing and one-job/one-output architectural patterns.

## Deliberately not copied

- feature-index tie breaking from the feasibility rank encoder;
- random one-start Lloyd-like medoid updater labelled as PAM;
- `k-means` versus relational PAM as a primary comparison;
- loaders that return `X` and labels together;
- shared append-only result CSV files;
- non-atomic multi-file job completion patterns;
- supervised gene-pair selection code.

The core implementation below is a clean implementation covered by the new
repository's MIT license. No source file from AIR was copied verbatim.
