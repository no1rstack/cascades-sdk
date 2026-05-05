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

5. Build and publish (pick one):

   **A — GitHub Actions (recommended, no upload token in GitHub secrets)**  
   One-time in PyPI → *cascades-sdk* → **Publishing** → **Add a new pending trusted publisher** → GitHub → `no1rstack/cascades-sdk` → workflow **`publish-pypi.yml`** → environment name empty (unless you uncomment `environment: pypi` in that workflow and create the same environment on GitHub).  
   Then **Actions** → **Publish to PyPI** → *Run workflow*. Set `dry_run` to true to only build and `twine check`.

   **B — Local machine**  
   Put **`PYPI_API_TOKEN`** or **`TWINE_USERNAME`** + **`TWINE_PASSWORD`** in a `.env`-style file (see **`README.md`** / `scripts/publish_pypi.ps1`). The script **clears `dist/`**, builds, then uploads **only** the wheel + sdist for the version in **`pyproject.toml`** (so old wheels never hit PyPI). Then:

   ```bash
   make build-dist
   python -m twine upload dist/cascades_sdk-<version>-*.whl dist/cascades_sdk-<version>.tar.gz
   ```

   Do **not** set **`PYPI_URL`** to a project page like `https://pypi.org/project/...` — use **`https://upload.pypi.org/legacy/`** for production, or omit **`PYPI_URL`** and let Twine default.

   On Windows you can run **`scripts/publish_pypi.ps1`** (defaults to `..\cascades\.env.local`, or set **`CASCADES_SDK_ENV_FILE`** / **`-EnvFile`**).

   PyPI does not allow re-uploading the same version — bump **`pyproject.toml`** and **`src/cascades_sdk/_meta.py`** (`__version__`) together before each release.

6. **Optional — npm scoped package (`@noirstack/cascades-sdk`)**  
   Publishes the mirrored **`contracts/api.yaml`**, **`LICENSE`**, and a small **ESM** entry (`index.js` / `index.d.ts`) for JS/TS tooling. **`package.json` → `files`** limits the tarball; **`prepublishOnly`** and **`prepack`** both run **`npm run build`** so publish never ships without a fresh copy of the contract and license.

   - **Version discipline:** from **`packages/cascades-sdk`**, use **`npm version patch`**, **`minor`**, or **`major`** (updates **`package.json`** and creates a git tag when run in a git checkout). Commit the version bump, then publish. CI today is **`workflow_dispatch`** only — add tag-based triggers in **`.github/workflows/publish-npm.yml`** only if you want automated publishes on specific tags.
   - **GitHub Actions:** add repository secret **`NPM_TOKEN`**, then **Actions → Publish npm @noirstack/cascades-sdk** (use `dry_run` to validate).
   - **Local:** **`npm login`** with an account that can publish to the **noirstack** org, then from the SDK repo **`npm publish -w @noirstack/cascades-sdk --access public`** (or **`scripts/publish_npm.ps1`**, which loads **`NPM_TOKEN`** / **`NODE_AUTH_TOKEN`** from the same **`-EnvFile` / `CASCADES_SDK_ENV_FILE`** defaults as **`publish_pypi.ps1`**, typically **`..\cascades\.env.local`**).
   - **Org ownership:** after publish, run **`npm access ls-packages noirstack`** and in the npm UI confirm **`@noirstack/cascades-sdk`** is under the org; grant the **developers** team read/write as needed. A missing package page or publish denial is usually **org membership / token scope**, not bad `package.json`.
