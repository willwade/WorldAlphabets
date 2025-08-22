# Project Guidelines

- This repository mixes Python and Node code. Development code to build the data stores are in pytthon, while the published library is in Node and Python. 
- Use uv from astral.sh for running scripts and checks.
- Use `uv run` for Python scripts and checks.
- Run `ruff check` and `mypy` on any Python files you modify.
- Run `npm test` when JavaScript files are changed.
- Keep lines under 88 characters when possible.
- Store generated alphabet JSON under `data/alphabets/`.
- Document significant script or data changes in `README.md`.

