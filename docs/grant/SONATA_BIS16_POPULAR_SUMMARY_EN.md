# Representation Adequacy and Transportable Relational Profiles

Omics studies measure the activity of thousands of genes or other molecules in
each patient. A common aim is to discover groups of people who may share disease
mechanisms. The resulting groups, however, depend strongly on how patients are
compared. We can compare measurement values directly, or ask which genes are
more active than others within the same patient. The second approach produces
simple rules such as “gene A is more active than gene B”. These rules may be
easier to interpret and less dependent on laboratory scale, but they are not
always better.

This project will determine **when each way of comparing patients is
supported**, and will then develop Transportable Relational Patient Profiles
where the evidence justifies them. Using only one discovery cohort, the
software will test comparisons based on values, ranks, gene-to-gene relations,
or a combination of these views. If none provides credible structure, the
software will be allowed to withhold clustering. For supported groups, it will
learn short profiles made of relations between molecular features. Such a
profile will provide a readable description of a group instead of an
artificial “average patient”.

The complete profile will then be frozen and applied to patients from
independent cohorts. New-patient data will not be used to retrain the method,
normalise cohorts jointly, or improve thresholds. A patient will be assigned
only when enough rules can be observed and the decision is sufficiently clear.
Otherwise the patient will remain unassigned. Uncertainty will therefore be
reported instead of being hidden by a forced decision.

The research will combine controlled simulations with independent lung and
colorectal cancer cohorts. In every primary comparison, different patient
representations will use the same deterministic clustering algorithm. We will
measure profile stability, length and readability, gene coverage across
platforms, resistance to perturbations, and agreement of frozen groups with
biological and clinical information. Disease labels and clinical outcomes will
be used only at the final evaluation stage.

Preliminary results show that different representations work best under
different conditions. They also reveal an important limitation: stable data
structure need not match a particular clinical label, and one of two transfer
directions between cohorts failed a threshold fixed in advance. The project
therefore does not assume that relations will always win. Its outcome will be a
set of methods and transparent rules defining when relational patient profiles
are credible, when measurement values should be retained, and when withholding
clustering is the honest conclusion.
