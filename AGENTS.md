# Project Guidelines

- This repository mixes Python and Node code. Development code to build the data stores are in pytthon, while the published library is in Node and Python. 
- Use uv from astral.sh for running scripts and checks.
- Use `uv run` for Python scripts and checks.
- Run `ruff check` and `mypy` on any Python files you modify. (NB: uv run mypy --install-types for types installation)
- Run `npm test` when JavaScript files are changed.
- Keep lines under 88 characters when possible.
- Store generated alphabet JSON under `data/alphabets/`.
- Note scripts are in `scripts/`. Many of these are used to generate data files. 
- Document significant script or data changes in `README.md`.
- A webUI which is built using vue+vite is in the `webui/` directory. Note its a static site with no backend. Hosted on github pages. (See workflows)

