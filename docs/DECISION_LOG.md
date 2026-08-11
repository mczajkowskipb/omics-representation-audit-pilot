# Decision log

## Frozen for PILOT-001--006

1. The protocol is authoritative and is stored byte-for-byte in this repository.
2. Feature selection is source-only MAD on observed source values, before
   imputation, with deterministic `feature_id` tie breaking.
3. Value preprocessing uses source medians and source IQRs; zero IQR uses a recorded `1.0` fallback.
4. Ties receive average ranks and missing states use an explicit mask.
5. Normalized Footrule uses the maximum Spearman Footrule `floor(p^2 / 2)`.
6. Relation Hamming is normalized over jointly observed, positive-weight relations only.
7. Hybrid scales are fitted only on source distance matrices.
8. Clustering uses one deterministic PAM BUILD+SWAP implementation for every representation.
9. `K` is an explicit experimental control and is never calculated from evaluation labels.

## Deferred scientific risk

A stable technical nuisance can be statistically indistinguishable from a
stable biological cluster when only `X` is available. Therefore the future
NULL/nuisance generator and Gate B interpretation must be reviewed before
PILOT-008--010. No batch-aware diagnostic is introduced in PILOT-001--006.

The GSE10072/GSE19804 transfer is also a combined biological and technical
stress test, because their normal-tissue definitions differ and GSE19804 has a
paired tumour/adjacent-normal design. This must be reflected in the later Gate C
interpretation.
