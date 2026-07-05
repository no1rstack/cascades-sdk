import * as vscode from 'vscode';
import * as https from 'https';
import * as http from 'http';

// ─── Constants ────────────────────────────────────────────

const DOCS_URL = 'https://cascades.work/docs';
const AUTH_URL = `${DOCS_URL}/authentication`;
const WORKFLOWS_URL = `${DOCS_URL}/workflows`;
const API_URL = `${DOCS_URL}/api`;
const GETTING_STARTED_URL = `${DOCS_URL}/getting-started`;
const EXAMPLES_URL = `${DOCS_URL}/examples`;
const BUILDER_URL = 'https://cascades.work/builder';
const DASHBOARD_URL = 'https://cascades.work/dashboard';
const GITHUB_URL = 'https://github.com/no1rstack/cascades-sdk';
const ISSUES_URL = `${GITHUB_URL}/issues`;

const CASCADES_VERSION = '2.3.0';
const EXTENSION_VERSION = '0.1.0';

// ─── Types ────────────────────────────────────────────────

interface CascadesConfig {
  baseUrl: string;
  sessionCookie?: string;
}

interface WorkflowDefinition {
  id: string;
  name: string;
  version?: string;
  description?: string;
  collectors?: string[];
  schedule?: string | null;
  status?: string;
}

interface WorkflowRunAccepted {
  runId: string;
  workflowId?: string;
  executionMode?: string;
  status?: string;
  message?: string;
}

interface RunResult {
  id?: string;
  runId?: string;
  status?: string;
  startedAt?: string;
  started_at?: string;
  completedAt?: string;
  completed_at?: string;
  error?: string;
}

// ─── Config ───────────────────────────────────────────────

function getConfig(): CascadesConfig {
  const config = vscode.workspace.getConfiguration('cascades');
  return {
    baseUrl: config.get<string>('baseUrl', 'https://cascades.work'),
    sessionCookie: config.get<string>('sessionCookie'),
  };
}

async function setSessionCookie(cookie: string): Promise<void> {
  const config = vscode.workspace.getConfiguration('cascades');
  await config.update('sessionCookie', cookie, vscode.ConfigurationTarget.Global);
}

async function setBaseUrl(url: string): Promise<void> {
  const config = vscode.workspace.getConfiguration('cascades');
  await config.update('baseUrl', url, vscode.ConfigurationTarget.Global);
}

// ─── HTTP Client ─────────────────────────────────────────

function apiRequest(
  baseUrl: string,
  method: string,
  path: string,
  body?: unknown,
  sessionCookie?: string,
): Promise<{ status: number; data: unknown }> {
  return new Promise((resolve, reject) => {
    const url = new URL(path, baseUrl);
    const isHttps = url.protocol === 'https:';
    const transport = isHttps ? https : http;

    const options: http.RequestOptions = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + url.search,
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': `cascades-vscode/${EXTENSION_VERSION}`,
      },
      timeout: 15000,
    };

    if (sessionCookie) {
      options.headers!['Cookie'] = `__session=${sessionCookie}`;
    }

    const req = transport.request(options, (res) => {
      let data = '';
      res.on('data', (chunk: Buffer) => { data += chunk.toString(); });
      res.on('end', () => {
        let parsed: unknown;
        try { parsed = JSON.parse(data); } catch { parsed = data; }
        resolve({ status: res.statusCode || 500, data: parsed });
      });
    });

    req.on('error', (err) => reject(new Error(`Connection failed: ${err.message}. Check your baseUrl and network.`)));
    req.on('timeout', () => { req.destroy(); reject(new Error('Request timed out. See: ' + API_URL)); });

    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

// ─── Helpers ─────────────────────────────────────────────

function getDocLink(section: string): string {
  return `${DOCS_URL}/${section}`;
}

function formatDocError(message: string, section: string): string {
  return `${message}\n  → Docs: ${getDocLink(section)}`;
}

async function checkAuth(): Promise<string | undefined> {
  const config = getConfig();
  if (!config.sessionCookie) {
    const action = await vscode.window.showWarningMessage(
      'Cascades: No session cookie configured. Set one first.',
      'Set Cookie',
      'Open Auth Docs',
    );
    if (action === 'Set Cookie') {
      await vscode.commands.executeCommand('cascades.authenticate');
    } else if (action === 'Open Auth Docs') {
      vscode.env.openExternal(vscode.Uri.parse(AUTH_URL));
    }
    return undefined;
  }
  return config.sessionCookie;
}

async function promptForInput(prompt: string, placeHolder: string, password = false): Promise<string | undefined> {
  return vscode.window.showInputBox({ prompt, placeHolder, ignoreFocusOut: true, password });
}

async function showResultInEditor(content: string, language: string, filename: string): Promise<void> {
  const doc = await vscode.workspace.openTextDocument({ content, language });
  await vscode.window.showTextDocument(doc, { preview: false });
}

// ─── Commands ────────────────────────────────────────────

async function gettingStarted(): Promise<void> {
  const panel = vscode.window.createWebviewPanel(
    'cascadesGettingStarted',
    'Cascades — Getting Started',
    vscode.ViewColumn.One,
    { enableScripts: true },
  );

  panel.webview.html = `<!DOCTYPE html>
<html lang="en">
<head>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    padding: 2rem; max-width: 800px; margin: 0 auto;
    color: var(--vscode-editor-foreground);
    background: var(--vscode-editor-background);
    line-height: 1.6;
  }
  h1 { font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem; }
  h2 { font-size: 1.1rem; font-weight: 600; margin-top: 2rem; margin-bottom: 0.5rem; }
  p { color: var(--vscode-descriptionForeground); margin-bottom: 0.75rem; }
  code {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.85rem;
    background: var(--vscode-textCodeBlock-background);
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
  }
  .step {
    background: var(--vscode-textBlockQuote-background);
    border-left: 3px solid var(--vscode-textLink-foreground);
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
  }
  .step h3 { margin-top: 0; margin-bottom: 0.25rem; font-size: 0.95rem; }
  .step p { margin: 0.25rem 0; }
  a { color: var(--vscode-textLink-foreground); }
  .badge { display: inline-block; font-size: 0.75rem; padding: 0.15rem 0.5rem; background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); border-radius: 4px; margin-right: 0.5rem; }
</style>
</head>
<body>
  <h1>🚀 Cascades — Getting Started</h1>
  <p>Version ${CASCADES_VERSION} · Extension v${EXTENSION_VERSION}</p>

  <div class="step">
    <h3><span class="badge">Step 1</span> Configure Authentication</h3>
    <p>Run <b>Cascades: Set Session Cookie</b> from the command palette (<code>Ctrl+Shift+P</code>).</p>
    <p>Get your cookie from <a href="#" onclick="openUrl('${AUTH_URL}')">${AUTH_URL}</a></p>
  </div>

  <div class="step">
    <h3><span class="badge">Step 2</span> Set Your Server URL</h3>
    <p>Settings → Extensions → Cascades → <code>cascades.baseUrl</code></p>
    <p>Default: <code>https://cascades.work</code></p>
  </div>

  <div class="step">
    <h3><span class="badge">Step 3</span> Try a Command</h3>
    <p>Run <b>Cascades: List Workflows</b> or <b>Cascades: Run OSINT Intake</b></p>
  </div>

  <div class="step">
    <h3><span class="badge">Step 4</span> Explore More</h3>
    <p>• <b>Cascades: Open Dashboard</b> — view workflows and runs</p>
    <p>• <b>Cascades: Open Workflow Builder</b> — visual DAG editor</p>
    <p>• <b>Cascades: Insert Code Example</b> — pasteable Python snippets</p>
  </div>

  <h2>📖 Resources</h2>
  <p><a href="#" onclick="openUrl('${DOCS_URL}')">Documentation</a></p>
  <p><a href="#" onclick="openUrl('${WORKFLOWS_URL}')">Workflow Guide</a></p>
  <p><a href="#" onclick="openUrl('${EXAMPLES_URL}')">Examples</a></p>
  <p><a href="#" onclick="openUrl('${ISSUES_URL}')">Report an Issue</a></p>

  <script>
    function openUrl(url) {
      const vscode = acquireVsCodeApi();
      vscode.postMessage({ command: 'openUrl', url });
    }
  </script>
</body>
</html>`;

  panel.webview.onDidReceiveMessage((message) => {
    if (message.command === 'openUrl') {
      vscode.env.openExternal(vscode.Uri.parse(message.url));
    }
  });
}

async function authenticate(): Promise<void> {
  const action = await vscode.window.showInformationMessage(
    'Cascades: To authenticate, get your session cookie from your Cascades deployment and paste it below.',
    'Get Session Cookie',
    'Open Auth Docs',
    'Cancel',
  );

  if (action === 'Get Session Cookie') {
    vscode.env.openExternal(vscode.Uri.parse(AUTH_URL));
  } else if (action === 'Open Auth Docs') {
    vscode.env.openExternal(vscode.Uri.parse(AUTH_URL));
    return;
  } else {
    return;
  }

  // Small delay to let the user see the docs, then prompt
  await new Promise(r => setTimeout(r, 500));

  const baseUrl = await promptForInput('Cascades server URL', 'https://cascades.work');
  if (baseUrl) {
    await setBaseUrl(baseUrl);
  }

  const cookie = await promptForInput('Paste your __session cookie value', 'eyJ...');
  if (cookie) {
    await setSessionCookie(cookie);
    vscode.window.showInformationMessage(formatDocError(
      'Cascades: Session cookie saved. Try running Cascades: List Workflows to verify.',
      'authentication',
    ));
  }
}

async function openDashboard(): Promise<void> {
  const config = getConfig();
  vscode.env.openExternal(vscode.Uri.parse(`${config.baseUrl}/dashboard`));
}

async function openBuilder(): Promise<void> {
  const config = getConfig();
  vscode.env.openExternal(vscode.Uri.parse(`${config.baseUrl}/builder`));
}

async function openDocumentation(): Promise<void> {
  const action = await vscode.window.showQuickPick(
    [
      { label: '📖 Getting Started', url: GETTING_STARTED_URL },
      { label: '🔑 Authentication', url: AUTH_URL },
      { label: '🔧 Workflows', url: WORKFLOWS_URL },
      { label: '📡 API Reference', url: API_URL },
      { label: '🧪 Examples', url: EXAMPLES_URL },
      { label: '🐛 Report Issue', url: ISSUES_URL },
    ],
    { placeHolder: 'Select documentation section' },
  );
  if (action) {
    vscode.env.openExternal(vscode.Uri.parse(action.url));
  }
}

async function listWorkflows(): Promise<void> {
  const cookie = await checkAuth();
  if (!cookie) return;

  const config = getConfig();
  vscode.window.showInformationMessage('Cascades: Fetching workflows...');

  try {
    const response = await apiRequest(config.baseUrl, 'GET', '/api/v1/workflows', undefined, cookie);

    if (response.status === 401) {
      const action = await vscode.window.showErrorMessage(
        formatDocError('Authentication failed. Your session cookie may be expired.', 'authentication'),
        'Re-authenticate',
      );
      if (action === 'Re-authenticate') await vscode.commands.executeCommand('cascades.authenticate');
      return;
    }

    const workflows = (response.data as any)?.workflows as WorkflowDefinition[] | undefined;
    if (!workflows || workflows.length === 0) {
      vscode.window.showInformationMessage('Cascades: No workflows found. Create one in the Builder.');
      return;
    }

    const items = workflows.map(w => ({
      label: `$(workflow) ${w.name || w.id}`,
      description: `v${w.version || '?'} · ${w.collectors?.join(', ') || 'no collectors'}`,
      detail: w.description || '',
      workflow: w,
    }));

    const picked = await vscode.window.showQuickPick(items, {
      placeHolder: `Select a workflow (${workflows.length} available)`,
      matchOnDetail: true,
    });

    if (picked) {
      showResultInEditor(
        JSON.stringify(picked.workflow, null, 2),
        'json',
        `workflow-${picked.workflow.id}.json`,
      );
    }
  } catch (err) {
    vscode.window.showErrorMessage(formatDocError(
      `Failed to list workflows: ${(err as Error).message}`,
      'troubleshooting',
    ));
  }
}

async function runOsintIntake(): Promise<void> {
  const cookie = await checkAuth();
  if (!cookie) return;

  const config = getConfig();

  const sourceTool = await vscode.window.showQuickPick(
    [
      { label: '🕷 SpiderFoot', value: 'spiderfoot' },
      { label: '🔗 Maltego', value: 'maltego' },
      { label: '🔍 Shodan', value: 'shodan' },
      { label: '🌐 Censys', value: 'censys' },
      { label: '📡 urlscan.io', value: 'urlscan' },
      { label: '🦠 VirusTotal', value: 'virustotal' },
      { label: '📋 WHOIS', value: 'whois' },
      { label: '🐙 GitHub', value: 'github' },
    ],
    { placeHolder: 'Select OSINT source', canPickMany: false },
  );

  if (!sourceTool) return;

  const connectorConfig: Record<string, unknown> = { sourceTool: sourceTool.value };
  const tool = sourceTool.value;

  if (tool === 'spiderfoot' || tool === 'shodan' || tool === 'censys' || tool === 'urlscan' || tool === 'virustotal' || tool === 'github') {
    const baseUrl = await promptForInput(`Enter the ${sourceTool.label} server/base URL`, `https://${tool}.example.com`);
    if (!baseUrl) return;
    connectorConfig.baseUrl = baseUrl;

    const apiKey = await promptForInput(`Enter your ${sourceTool.label} API key`, '', true);
    if (!apiKey) return;
    connectorConfig.apiKey = apiKey;

    if (tool === 'shodan') {
      const query = await promptForInput('Shodan search query (optional)', 'hostname:example.com');
      if (query) connectorConfig.query = query;
    }
    if (tool === 'virustotal') {
      const vtType = await vscode.window.showQuickPick(
        [{ label: 'IP', value: 'ip' }, { label: 'Domain', value: 'domain' }, { label: 'URL', value: 'url' }, { label: 'Hash', value: 'hash' }],
        { placeHolder: 'VirusTotal indicator type' },
      );
      if (vtType) { connectorConfig.type = vtType.value; }
    }
  } else if (tool === 'maltego') {
    const filePath = await promptForInput('Path to Maltego export file', '/path/to/export.csv');
    if (!filePath) return;
    connectorConfig.filePath = filePath;
    connectorConfig.fileFormat = 'csv';
  } else if (tool === 'whois') {
    const target = await promptForInput('WHOIS target domain/IP', 'example.com');
    if (!target) return;
    connectorConfig.target = target;
  } else if (tool === 'github') {
    const token = await promptForInput('GitHub Personal Access Token', '', true);
    if (!token) return;
    connectorConfig.apiKey = token;
    const query = await promptForInput('GitHub search query', 'org:no1rstack osint');
    if (query) connectorConfig.query = query;
  }

  const investigationId = await promptForInput('Judicium investigation ID (optional)', 'inv-...');
  if (investigationId) connectorConfig.investigationId = investigationId;

  vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: 'Cascades: Running OSINT intake...', cancellable: true },
    async (progress, token) => {
      token.onCancellationRequested(() => { vscode.window.showWarningMessage('Cascades: OSINT intake cancelled.'); });

      try {
        progress.report({ message: 'Submitting workflow...' });

        const body = {
          connectors: [connectorConfig],
          deduplicate: true,
          autoSubmit: true,
        };
        if (investigationId) (body as any).investigationId = investigationId;

        const response = await apiRequest(
          config.baseUrl,
          'POST',
          '/api/v1/osint/intake',
          body,
          cookie,
        );

        if (response.status === 401) {
          vscode.window.showErrorMessage(formatDocError('Session expired. Re-authenticate.', 'authentication'));
          return;
        }

        progress.report({ message: 'Processing complete.' });

        const result = response.data as Record<string, unknown>;
        const totalCollected = result.totalCollected ?? '?';
        const newFindings = result.newFindings ?? '?';
        const duplicatesSkipped = result.duplicatesSkipped ?? '?';
        const submittedToJudicium = result.submittedToJudicium ?? '?';

        const detail = `Collected: ${totalCollected} | New: ${newFindings} | Duplicates skipped: ${duplicatesSkipped} | Submitted: ${submittedToJudicium}`;
        vscode.window.showInformationMessage(`Cascades: OSINT intake complete. ${detail}`);

        showResultInEditor(JSON.stringify(result, null, 2), 'json', `cascades-osint-${Date.now()}.json`);
      } catch (err) {
        vscode.window.showErrorMessage(formatDocError(
          `OSINT intake failed: ${(err as Error).message}`,
          'workflows',
        ));
      }
    },
  );
}

async function runInvestigation(): Promise<void> {
  const cookie = await checkAuth();
  if (!cookie) return;

  const config = getConfig();

  const investigationId = await promptForInput('Judicium investigation ID', 'inv-123456');
  if (!investigationId) return;

  const sourcesInput = await promptForInput('Source URLs (comma-separated, optional)', 'https://feeds.example.com/rss');
  const sources = sourcesInput ? sourcesInput.split(',').map(s => s.trim()).filter(Boolean) : undefined;

  vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: 'Cascades: Running investigation...' },
    async (_progress) => {
      try {
        const response = await apiRequest(config.baseUrl, 'POST', `/api/v1/workflows/investigation-workflow/run`, {
          investigationId,
          sources,
        }, cookie);

        const result = response.data as Record<string, unknown>;
        vscode.window.showInformationMessage(
          `Cascades: Investigation complete. Report: ${result.reportId || '—'} | Proofs: ${(result.proofIds as string[])?.length || 0}`,
        );
        showResultInEditor(JSON.stringify(result, null, 2), 'json', `investigation-${investigationId}.json`);
      } catch (err) {
        vscode.window.showErrorMessage(formatDocError(
          `Investigation failed: ${(err as Error).message}`,
          'workflows/investigation',
        ));
      }
    },
  );
}

async function verifyEvidence(): Promise<void> {
  const cookie = await checkAuth();
  if (!cookie) return;

  const config = getConfig();

  const evidenceId = await promptForInput('Evidence ID to verify', 'ev-789');
  if (!evidenceId) return;

  const caseId = await promptForInput('Case/Investigation ID', 'case-456');
  if (!caseId) return;

  vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: 'Cascades: Verifying evidence...' },
    async () => {
      try {
        const response = await apiRequest(config.baseUrl, 'POST', `/api/v1/workflows/evidence-verification/run`, {
          evidenceId,
          caseId,
        }, cookie);

        const result = response.data as Record<string, unknown>;
        const verified = result.verified ? '✅ Verified' : '❌ Failed';
        vscode.window.showInformationMessage(
          `Cascades: Evidence verification ${verified}. Proof: ${result.proofId || '—'}`,
        );
        showResultInEditor(JSON.stringify(result, null, 2), 'json', `evidence-proof-${evidenceId}.json`);
      } catch (err) {
        vscode.window.showErrorMessage(formatDocError(
          `Evidence verification failed: ${(err as Error).message}`,
          'workflows/evidence-verification',
        ));
      }
    },
  );
}

async function showRunStatus(): Promise<void> {
  const cookie = await checkAuth();
  if (!cookie) return;

  const config = getConfig();

  const runId = await promptForInput('Execution / Run ID', 'exec-... or dag-...');
  if (!runId) return;

  try {
    const response = await apiRequest(config.baseUrl, 'GET', `/api/runs/${runId}`, undefined, cookie);

    if (response.status === 404) {
      // Try the /api/v1/executions path as fallback
      const altResponse = await apiRequest(config.baseUrl, 'GET', `/api/v1/executions/${runId}`, undefined, cookie);
      if (altResponse.status === 404) {
        vscode.window.showWarningMessage(formatDocError(`Run not found: ${runId}`, 'workflows'));
        return;
      }
      const result = altResponse.data as RunResult;
      vscode.window.showInformationMessage(`Cascades: Run ${runId} status: ${result.status || 'unknown'}`);
      showResultInEditor(JSON.stringify(result, null, 2), 'json', `run-${runId}.json`);
      return;
    }

    const result = response.data as RunResult;
    vscode.window.showInformationMessage(`Cascades: Run ${runId} status: ${result.status || 'unknown'}`);
    showResultInEditor(JSON.stringify(result, null, 2), 'json', `run-${runId}.json`);
  } catch (err) {
    vscode.window.showErrorMessage(formatDocError(
      `Failed to get run status: ${(err as Error).message}`,
      'api',
    ));
  }
}

async function insertExample(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('Open a Python file first, then run this command.');
    return;
  }

  const example = await vscode.window.showQuickPick(
    [
      { label: '🕷 SpiderFoot OSINT Collection', description: 'Poll SpiderFoot and submit findings', value: 'spiderfoot' },
      { label: '🔗 Maltego Import', description: 'Parse a Maltego CSV export', value: 'maltego' },
      { label: '🔬 Full Investigation Pipeline', description: 'Collect → Analyze → Report', value: 'investigation' },
      { label: '🔐 Evidence Verification', description: 'Generate Hexarch proof', value: 'evidence' },
      { label: '📐 DAG Compilation', description: '@task/@flow decorators', value: 'dag' },
      { label: '⏰ Cron Scheduling', description: 'Schedule recurring workflows', value: 'cron' },
      { label: '⚠️ Error Handling', description: 'Try/except with doc links', value: 'error' },
    ],
    { placeHolder: 'Select an example to insert' },
  );

  if (!example) return;

  const snippets: Record<string, string> = {
    spiderfoot: `# ── SpiderFoot OSINT Collection ──
# Docs: ${WORKFLOWS_URL}/connectors#spiderfoot

from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.workflows import submit_and_wait

client = CascadesClient("${getConfig().baseUrl}", SessionCookieAuth("YOUR_SESSION"))
result = submit_and_wait(client, "osint-intake", {
    "connectors": [{
        "sourceTool": "spiderfoot",
        "baseUrl": "http://localhost:5001",
        "apiKey": "YOUR_API_KEY",
    }],
})
print(f"Findings: {result}")
`,
    maltego: `# ── Maltego Import ──
# Docs: ${WORKFLOWS_URL}/connectors#maltego

from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.workflows import submit_and_wait

client = CascadesClient("${getConfig().baseUrl}", SessionCookieAuth("YOUR_SESSION"))
result = submit_and_wait(client, "osint-intake", {
    "connectors": [{
        "sourceTool": "maltego",
        "filePath": "export.csv",
        "fileFormat": "csv",
    }],
})
print(f"Entities: {result.get('newFindings')}")
`,
    investigation: `# ── Full Investigation Pipeline ──
# Docs: ${WORKFLOWS_URL}/investigation

from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.workflows import run_investigation

client = CascadesClient("${getConfig().baseUrl}", SessionCookieAuth("YOUR_SESSION"))
result = run_investigation(client, "inv-123", sources=["https://feeds.example.com/rss"])
print(f"Report: {result.get('reportId')}")
print(f"Proofs: {result.get('proofIds')}")
`,
    evidence: `# ── Evidence Verification with Hexarch Proof ──
# Docs: ${WORKFLOWS_URL}/evidence-verification

from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.workflows import verify_evidence

client = CascadesClient("${getConfig().baseUrl}", SessionCookieAuth("YOUR_SESSION"))
result = verify_evidence(client, evidence_id="ev-789", case_id="case-456")
print(f"Verified: {result.get('verified')}")
print(f"Proof ID: {result.get('proofId')}")
`,
    dag: `# ── DAG Compilation with @task/@flow ──
# Docs: ${WORKFLOWS_URL}/dag

from cascades_sdk import task, flow
from cascades_sdk.compiler import build_dag_from_flow, canonical_json

@task
def fetch(ip: str) -> str: return f"report for {ip}"

@task
def enrich(ip: str) -> str: return f"shodan for {ip}"

@task
def merge(ip: str, a: str, b: str) -> dict:
    return {"ip": ip, "report": a, "shodan": b}

@flow
def pipeline(ip: str) -> dict:
    r = fetch(ip)
    s = enrich(ip)
    return merge(ip, r, s)

dag = build_dag_from_flow(pipeline, {"ip": "8.8.8.8"})
print(canonical_json(dag))
`,
    cron: `# ── Schedule a Recurring Workflow ──
# Docs: ${WORKFLOWS_URL}/scheduling

import requests

response = requests.post(
    "${getConfig().baseUrl}/api/v1/triggers",
    json={
        "workflowId": "osint-intake",
        "schedule": "0 * * * *",
        "inputs": {"connectors": [{"sourceTool": "spiderfoot", "baseUrl": "http://localhost:5001", "apiKey": "..."}]},
    },
    cookies={"__session": "YOUR_SESSION"},
)
print(response.json())
`,
    error: `# ── Error Handling with Doc Links ──
# Docs: ${WORKFLOWS_URL}/troubleshooting

from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.errors import AuthenticationError, NotFoundError, TimeoutError
from cascades_sdk.workflows import submit_and_wait

client = CascadesClient("${getConfig().baseUrl}", SessionCookieAuth("YOUR_SESSION"))

try:
    result = submit_and_wait(client, "osint-intake", {"connectors": [...]})
except AuthenticationError as e:
    print(f"Auth failed — re-login at ${AUTH_URL}")
    print(e)
except NotFoundError as e:
    print(f"Workflow not found — check catalog at ${WORKFLOWS_URL}")
except TimeoutError as e:
    print(f"Timed out — increase timeout or check ${WORKFLOWS_URL}/troubleshooting")
`,
  };

  const snippet = snippets[example.value];
  if (snippet) {
    editor.edit((editBuilder) => {
      editBuilder.insert(editor.selection.active, snippet);
    });
  }
}

async function about(): Promise<void> {
  vscode.window.showInformationMessage(
    `Cascades VS Code Extension v${EXTENSION_VERSION}\nPlatform: Cascades ${CASCADES_VERSION}\nDocs: ${DOCS_URL}\nRepo: ${GITHUB_URL}`,
  );
}

// ─── Activation ───────────────────────────────────────────

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand('cascades.gettingStarted', gettingStarted),
    vscode.commands.registerCommand('cascades.authenticate', authenticate),
    vscode.commands.registerCommand('cascades.openDashboard', openDashboard),
    vscode.commands.registerCommand('cascades.openBuilder', openBuilder),
    vscode.commands.registerCommand('cascades.showDocumentation', openDocumentation),
    vscode.commands.registerCommand('cascades.listWorkflows', listWorkflows),
    vscode.commands.registerCommand('cascades.runOsintIntake', runOsintIntake),
    vscode.commands.registerCommand('cascades.runInvestigation', runInvestigation),
    vscode.commands.registerCommand('cascades.verifyEvidence', verifyEvidence),
    vscode.commands.registerCommand('cascades.showRunStatus', showRunStatus),
    vscode.commands.registerCommand('cascades.insertExample', insertExample),
    vscode.commands.registerCommand('cascades.about', about),
  );
}

export function deactivate(): void {}
