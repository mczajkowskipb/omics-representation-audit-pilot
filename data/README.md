# Data policy

Large reference datasets are not duplicated here. Later adapters will use
configured, read-only paths to the two reference repositories.

Fitting manifests must point only to expression matrices and non-label schema
metadata. Evaluation-label paths belong to evaluation-only configuration and
must never be loaded by preprocessing, representation, distance, clustering,
or audit code.
