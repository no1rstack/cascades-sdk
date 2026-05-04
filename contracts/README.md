# HTTP contract mirror (`contracts/api.yaml`)

## Do not edit manually

`api.yaml` here must match the Cascades **platform** repository file (source of truth):

**[`no1rstack/cascades` → `contracts/api.yaml`](https://github.com/no1rstack/cascades/blob/main/contracts/api.yaml)**

## How to sync (one command)

From the SDK repo root, with the platform repo available locally:

```bash
./scripts/sync_contract.sh ../cascades/contracts/api.yaml
# default source is ../cascades/contracts/api.yaml:
./scripts/sync_contract.sh
```

Windows (PowerShell):

```powershell
.\scripts\sync_contract.ps1
# or: .\scripts\sync_contract.ps1 'C:\path\to\cascades\contracts\api.yaml'
```

Cross-platform (Python only):

```bash
python scripts/sync_contract.py ../cascades/contracts/api.yaml
# or: make sync-contract
```

Sync **normalizes line endings to LF** on write (see repo `.gitattributes`) and then runs the verifier against the source path you copied from.

## How CI enforces it

GitHub Actions checks out **`no1rstack/cascades`** at:

- **`contracts/UPSTREAM_COMMIT`** (first non-empty, non-`#` line) when that file is present — use a **full SHA** for release integrity; or
- **`main`** when `UPSTREAM_COMMIT` is absent or empty.

It then runs `python scripts/verify_contract_mirror.py --against ../platform/contracts/api.yaml` (no raw GitHub URL in CI).

If the platform repo is not readable with the job token, add a repository secret **`CASCADES_READ_TOKEN`** (PAT with `contents: read` on `no1rstack/cascades`). The workflow maps that to **`CASCADES_TOKEN`** and uses an explicit non-empty check before falling back to **`github.token`**.

**Fork PRs:** the contract job **skips** cloning the private platform repo (forks cannot use the base repo’s secrets). Maintainers should validate from a branch on the upstream repo before merge.

## Optional: pin platform revision

See **`UPSTREAM_COMMIT.example`**. Copy to **`UPSTREAM_COMMIT`** and commit a single ref (SHA / tag / branch) when you want CI (and reproducible diffs) pinned to that platform revision — e.g. before tagging an SDK release.

## Optional: pre-commit drift guard

See **`scripts/git-hooks/README.md`**.
