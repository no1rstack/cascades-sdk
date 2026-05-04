.PHONY: sync-contract verify-contract verify-contract-local

sync-contract:
	python scripts/sync_contract.py

# Uses remote fetch (public platform repo only); for a local clone use verify-contract-local.
verify-contract:
	python scripts/verify_contract_mirror.py

verify-contract-local:
	python scripts/verify_contract_mirror.py --against ../cascades/contracts/api.yaml
