# Optional Git hooks

## `pre-commit-contract` (drift guard)

Copy the sample into your local clone so you cannot commit a stale `contracts/api.yaml` when a sibling `cascades` checkout exists:

```bash
cp scripts/git-hooks/pre-commit-contract.sample .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

If `../cascades/contracts/api.yaml` is missing, the hook **skips** with a short notice (“Skipping contract check…”) so CI and machines without the platform repo still work.

Point at a non-default platform tree:

```bash
export CASCADES_PLATFORM_CONTRACT=/path/to/cascades/contracts/api.yaml
```

Windows (Git Bash): same commands. For PowerShell-only hooks, call `python scripts/verify_contract_mirror.py --against ...` from a `pre-commit` script you maintain yourself.
