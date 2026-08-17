# Preliminary results — insertion-ready English draft

## Source-only representation audit

We developed a deterministic Python reference pipeline for comparing value, rank-relational and hybrid representations before clustering. All candidate representations used the same deterministic PAM implementation, thereby separating the effect of representation from the effect of the clustering engine. Source preprocessing, median-absolute-deviation feature selection, relation screening, distance scaling, representation selection and medoid fitting were completed without access to evaluation labels. The labels were used only after all source-only decisions and assignments had been frozen. The implementation additionally permits a `NO_STABLE_STRUCTURE` outcome rather than forcing a partition when source stability does not exceed a matched NULL threshold.

The primary controlled benchmark comprised 630 independently evaluated source-target pairs spanning VALUE, RELATIONAL, HYBRID and NULL regimes, signal strengths and domain shifts. The audit identified the generating representation family in 93.3% of signal replicates. Median target ARI regret relative to the retrospectively best representation was 0.000. The false-structure rate under NULL was 6.7%, and HYBRID was selected in 0% of pure VALUE or RELATIONAL regimes. Differences in source-only audit quality were strongly associated with the corresponding differences in target performance (Spearman rho = 0.854). All five preregistered Gate B criteria were met without changing thresholds after target evaluation.

## Real-data behaviour

We next performed source-only within-dataset audits on eleven heterogeneous expression datasets. Before any labels were loaded, the complete audit decision and assignments for all eleven datasets were written to immutable, hashed prelabel artifacts. RELATIONAL was selected for eight datasets, VALUE for two and HYBRID for one. The selected method was within 0.05 ARI of the retrospective within-dataset oracle in 9/11 datasets, and median ARI regret was 0.011. However, median ARI of the selected clustering against the available labels was only 0.065. Thus, the audit often chose a geometry close to the best candidate geometry, but stable unsupervised structure did not necessarily correspond to the available clinical or diagnostic label. These results are descriptive and are not treated as external validation.

## Frozen external transfer

We evaluated bidirectional frozen transfer between the independent lung-expression cohorts GSE10072 and GSE19804. Each direction used 200 features selected by source-only MAD within the predeclared universe of 22,277 common probe identifiers. All preprocessing parameters, relation candidates, distance scales, selected representation, medoids and rejection thresholds were frozen before target labels were evaluated. Target samples were assigned independently without target refitting or joint source-target normalisation.

For GSE19804→GSE10072, the source-only audit selected a relational pair-Hamming representation and achieved target ARI 0.926, identical to the retrospective oracle (regret 0.000). For GSE10072→GSE19804, it selected a value-correlation representation and achieved ARI 0.559, compared with oracle ARI 0.664 (regret 0.105284). Assignment coverage was above 0.80 and cluster-size requirements were satisfied in both directions, but the second regret exceeded the frozen reverse-direction allowance of 0.10 by 0.005284. The formal Gate C decision therefore remained STOP. No post-label adjustment of thresholds, features, relation margins, hybrid weights or selection rules was performed.

## Consequence for the proposed project

The pilot supports the existence of distinct representation-competence regimes and demonstrates that a source-only audit can be informative under controlled shifts. At the same time, it identifies the central unresolved problem: representation adequacy and cross-cohort biological transportability cannot be inferred from within-cohort stability alone. We therefore do not present automatic representation selection as already established across cohorts. Instead, the proposed project will (i) map explicit applicability boundaries, (ii) validate across multiple independent cohorts per disease context, and (iii) learn sparse relational regions directly rather than treating post-hoc rules as evidence of transportability.

The pilot deliberately stopped before direct relational regions and anchor restrictions because the preregistered external-transfer gate was not met. Consequently, direct regions: NOT TESTED; anchors: NOT TESTED. These components are prospective, falsifiable research tasks with their own GO/STOP criteria, rather than preliminary achievements.

## Compact numerical table

| Analysis | Frozen result | Interpretation |
|---|---:|---|
| Controlled source-target pairs | 630 | complete primary simulation grid |
| Exact family identification | 0.933 | Gate B criterion met |
| Median target ARI regret | 0.000 | Gate B criterion met |
| NULL false-structure rate | 0.067 | Gate B criterion met |
| HYBRID selection in pure regimes | 0.000 | Gate B criterion met |
| Source/target Spearman association | 0.854 | Gate B criterion met |
| Real within-dataset audits | 11 | descriptive only |
| Selected within 0.05 ARI of oracle | 9/11 | representation ranking often near oracle |
| Median selected real-data ARI | 0.065 | stability does not guarantee label agreement |
| GSE19804→GSE10072 | ARI 0.926; regret 0.000 | strong direction |
| GSE10072→GSE19804 | ARI 0.559; regret 0.105284 | frozen limit narrowly exceeded |
| Gate B | GO | controlled evidence supported |
| Gate C | STOP | no threshold relaxation or target retuning |
