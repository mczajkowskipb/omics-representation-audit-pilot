from __future__ import annotations

import os
import subprocess
import sys


PROBE = r'''
import sys
import numpy as np
from rep_audit.data.schema import DatasetBundle
from rep_audit.preprocessing.robust import fit_source_preprocessing

source = DatasetBundle(
    X=np.array([[0.0, 3.0, 1.0], [1.0, 3.0, 2.0], [2.0, 3.0, 4.0]]),
    sample_ids=("s1", "s2", "s3"),
    feature_ids=("g1", "g2", "g3"),
    dataset_id="probe",
    platform_id="sim",
    cohort_id="source",
)
artifact = fit_source_preprocessing(source, feature_budget=2)
sys.stdout.buffer.write(artifact.to_json_bytes())
'''


def test_independent_processes_emit_byte_identical_artifact() -> None:
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "NUMBA_NUM_THREADS": "1",
        }
    )
    first = subprocess.check_output([sys.executable, "-c", PROBE], env=environment)
    second = subprocess.check_output([sys.executable, "-c", PROBE], env=environment)
    assert first == second
