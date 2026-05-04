# SDK release checklist

Contract changes always flow **platform → SDK** (never edit `contracts/api.yaml` by hand here).

1. **Sync the mirror** (after the platform PR that updates `contracts/api.yaml` is merged — or from your local platform tree):

   ```bash
   ./scripts/sync_contract.sh ../cascades/contracts/api.yaml
   # or: make sync-contract
   ```

2. **Confirm CI contract job** passes on your branch (it checks out `no1rstack/cascades` and diffs `contracts/api.yaml`).

3. **Optional — pin platform for this release**  
   To avoid races with `main`, add `contracts/UPSTREAM_COMMIT` containing a single revision (full SHA recommended). CI will check out that ref when cloning the platform repo. See `contracts/UPSTREAM_COMMIT.example`. Remove or update the file when you intentionally move to a newer platform revision.  
   **If `UPSTREAM_COMMIT` is present,** confirm it names the same platform revision you used to produce this release’s `contracts/api.yaml` (re-sync from that checkout or from `main` after verifying the SHA on GitHub).

4. **Bump version** in `pyproject.toml` **after** the contract is synced and verified (not before).

5. Build and publish:

   ```bash
   python -m build
   python -m twine check dist/*
   python -m twine upload dist/*
   ```

   On Windows you can instead run **`scripts/publish_pypi.ps1`** (loads `PYPI_*` / `TWINE_*` from a `.env`-style file; see root **README**). PyPI does not allow re-uploading the same version — bump **`pyproject.toml`** and **`src/cascades_sdk/__init__.py`** (`__version__`) together before each release.
