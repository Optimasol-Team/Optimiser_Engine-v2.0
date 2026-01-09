# Domain unit tests

- Run from the repository root: `pip install -e .`, `pytest -q`, or `pytest -q tests/unit/domain`.
- Shared fixtures live in `tests/unit/domain/conftest.py`.
- Submodels are exercised first (time slots, setpoints/planning, consumption profiles/constraints, features/prices, water heater), followed by `Client` factory/serialization tests and a light example YAML sanity check.
