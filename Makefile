# Cholsey Parish Sustainability Dashboard — maintainer interface.
#
# This is the whole command surface a non-specialist maintainer needs
# (docs/development-plan.md §7 non-functional requirements, and CLAUDE.md).
# `refresh` and `site` are stubs until Phase 2 (data ingestion) and Phase 4
# (front-end skeleton wired to real data) land — see docs/STATUS.md for the
# current phase.

.PHONY: setup test lint refresh site clean

setup:
	cd pipeline && uv sync
	cd web && npm install

test:
	cd pipeline && uv run pytest
	cd web && npm run test

lint:
	cd pipeline && uv run ruff check . && uv run ruff format --check .
	cd web && npm run lint

# Fetch → validate → geographic join → validate → export (development-plan.md
# §2.4). Not yet implemented — lands in Phase 2/3.
refresh:
	@echo "make refresh: not yet implemented (Phase 2/3, see docs/STATUS.md)"
	@exit 1

# Build the static site from the current data/processed/ export
# (development-plan.md §2.4). Currently builds the placeholder skeleton only.
site:
	cd web && npm run build

clean:
	rm -rf pipeline/.venv pipeline/.pytest_cache pipeline/.ruff_cache
	rm -rf web/node_modules web/dist web/.astro
