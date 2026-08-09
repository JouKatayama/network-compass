# Synthetic Data Generator

NC-003 provides deterministic `demo` and `edge_cases` fact datasets. It generates canonical people, context facts, project participation, and immutable interaction events plus a separate scenario-expectation manifest. It never writes derived `RelationshipState` into source facts.

From the repository root:

```bash
make synthetic-demo
make synthetic-edge-cases
```

Each command writes `dataset.json`, `summary.json`, and `validation-report.json` below `tools/synthetic-data/output/<family>/`. Output is reproducible for the fixed default seed and version and is intentionally ignored by Git.

Relationship-state checks for P001/P018/P102 remain `PENDING_NC_004` until the Relationship Engine exists. All structural checks must pass now.
