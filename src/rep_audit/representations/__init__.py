"""Value-independent rank and relation representations."""

from rep_audit.representations.ranks import RankRepresentation, average_rank_encode
from rep_audit.representations.ternary_relations import (
    TernaryRelationRepresentation,
    encode_ternary_relations,
)

__all__ = [
    "RankRepresentation",
    "TernaryRelationRepresentation",
    "average_rank_encode",
    "encode_ternary_relations",
]
