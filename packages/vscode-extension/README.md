# Cascades (VS Code Extension)

OSINT workflow engine for the Noir Stack platform. Submit workflows, poll connectors, verify evidence, and manage OSINT pipelines directly from VS Code.

## Features

- **Cascades: Getting Started** — guided onboarding walkthrough
- **Cascades: Set Session Cookie** — authenticate with your Cascades deployment
- **Cascades: Open Dashboard** — view workflows, triggers, and run history
- **Cascades: Open Workflow Builder** — visual DAG editor for OSINT pipelines
- **Cascades: List Workflows** — browse the workflow catalog
- **Cascades: Run OSINT Intake** — guided collection from SpiderFoot, Maltego, Shodan, Censys, urlscan.io, VirusTotal, WHOIS, or GitHub
- **Cascades: Run Investigation** — full pipeline: collect → analyze → report
- **Cascades: Verify Evidence** — generate cryptographic proofs via Hexarch
- **Cascades: Show Run Status** — check execution results by run ID
- **Cascades: Insert Code Example** — pasteable Python snippets for common workflows
- **Cascades: Open Documentation** — quick section picker with all doc URLs

All error messages include links to the relevant documentation for quick troubleshooting.

## Commands

| Command | Description |
|---|---|
| `Cascades: Getting Started` | Onboarding walkthrough with setup steps |
| `Cascades: Set Session Cookie` | Authenticate with your deployment |
| `Cascades: Open Dashboard` | Opens the web dashboard |
| `Cascades: Open Workflow Builder` | Opens the visual DAG builder |
| `Cascades: List Workflows` | Browse the workflow catalog |
| `Cascades: Run OSINT Intake` | Guided OSINT collection |
| `Cascades: Run Investigation` | Full investigation pipeline |
| `Cascades: Verify Evidence` | Generate cryptographic proofs |
| `Cascades: Show Run Status` | Check execution results |
| `Cascades: Open Documentation` | Quick section picker |
| `Cascades: Insert Code Example` | Pasteable Python snippets |
| `Cascades: About` | Version and links |

## Configuration

| Setting | Default | Description |
|---|---|---|
| `cascades.baseUrl` | `https://cascades.work` | Your Cascades deployment URL |
| `cascades.sessionCookie` | — | Auth0 session cookie (set via the Authenticate command) |

## Links

- Cascades Platform: https://cascades.work
- Documentation: https://cascades.work/docs
- Company: https://noirstack.com
- Support: https://github.com/no1rstack/cascades-sdk/issues
- GitHub: https://github.com/no1rstack/cascades-sdk
- Extension Repository: `packages/vscode-extension/`

## Publishing

From repository root:

1. Install dependencies: `npm install`
2. Compile extension: `npm run build:extension`
3. Package VSIX: `npm run package -w packages/vscode-extension`
4. Publish: `npm run publish -w packages/vscode-extension`
