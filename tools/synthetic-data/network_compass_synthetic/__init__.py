"""Deterministic synthetic fact generation for Network Compass."""

from network_compass_synthetic.generator import (
    DEFAULT_SEED,
    generate_dataset,
)
from network_compass_synthetic.models import SyntheticDataset
from network_compass_synthetic.validation import validate_dataset

__all__ = ["DEFAULT_SEED", "SyntheticDataset", "generate_dataset", "validate_dataset"]
