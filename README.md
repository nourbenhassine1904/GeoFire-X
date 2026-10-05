# GeoFire-X

Multimodal Spatio-Temporal Deep Learning for Next-Day Wildfire Spread Forecasting under Geographic and Temporal Domain Shift.

## Current Phase

Phase 1 — Reproducible Experimental Foundation

The repository currently contains the shared project structure and experimental
contracts. Phase 1 will establish reproducible data preparation, evaluation, and
a persistence baseline before advanced model training begins.

See [Project Context](docs/PROJECT_CONTEXT.md) for the scientific objective,
input and target contracts, scope, and experimental rules.

## Primary Dataset

WildfireSpreadTS

## Team

4 Data Science / AI engineering students

## Scientific Pipeline

Data Audit → Event-Level Split → DataLoader → Persistence Baseline → Metrics → ID/OOD Evaluation → Multimodal & Temporal Modeling → Robustness

ID/OOD refers to in-distribution and out-of-distribution evaluation.

## Repository Structure

| Directory | Purpose |
| --- | --- |
| `data/` | Local raw, interim, and processed datasets; tracked metadata in `manifests/`. Dataset contents are ignored by Git. |
| `notebooks/` | Exploratory analysis and data audit notebooks. |
| `src/geofirex/` | Shared Python package for reusable project code. |
| `scripts/` | Reproducible command-line workflows. |
| `tests/` | Checks for data contracts, leakage prevention, and project behavior. |
| `splits/` | Versioned event-level train/validation/test assignments. |
| `configs/` | Shared data and experiment configurations. |
| `reports/` | Evaluation reports and figures in `figures/`. |
| `docs/` | Scientific context and project documentation. |

Empty directories contain `.gitkeep` placeholders so Git preserves the structure.
Keep manifests and split definitions small and versioned; keep datasets and
model artifacts outside Git.

## Collaboration Workflow

- Keep `main` stable and ready for the whole team to use.
- Develop each contribution on a focused feature branch created from `main`.
- Submit contributions through a Pull Request with a clear description and relevant validation.
- Have another student review the Pull Request before merging.
- Never commit large datasets, checkpoints, or experiment artifacts to Git.

Assign each wildfire event to exactly one split: no day from a training event
may appear in validation or test. Every experiment must record its dataset
version, split version, configuration, random seed, and Git commit.
