.PHONY: sync-contract verify-contract verify-contract-local build-dist

sync-contract:
	python scripts/sync_contract.py

# Source dist + wheel under dist/ (clean first for a reproducible release tree).
build-dist:
	rm -rf dist build src/*.egg-info
	python -m pip install -q build twine
	python -m build
	python -m twine check dist/*

# Uses remote fetch (public platform repo only); for a local clone use verify-contract-local.
verify-contract:
	python scripts/verify_contract_mirror.py

verify-contract-local:
	python scripts/verify_contract_mirror.py --against ../cascades/contracts/api.yaml
