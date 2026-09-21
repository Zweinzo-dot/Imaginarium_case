# Alaga Evidence Review

For interviewers: start with [the reviewer walkthrough](REVIEWER_GUIDE.md) and [verification notes](VALIDATION.md). Source and bundled demo artifacts are in this repository. Public hosting is being configured; a live link will be added after signed-out access is verified.

A working Python + Streamlit + Pandas prototype for testing Alaga's early customer hypotheses against what customers **say**, what they **do**, and what external **research** suggests.

It starts with the six customer-pain hypotheses and working ICP from **Alaga pitch deck v10, slides 4–5**. AI can analyze the whole customer base, propose source-linked classifications, and draft conclusions for each workspace area. A person approves, edits, or rejects them and separately records strategic decisions. There is no automated ICP confidence score or automatic double-down/pivot/stop decision.

**All customers, action records, and interviews are fictional.** The four bundled external research summaries cite real publications and clearly state their limitations. The demo is not evidence of Alaga traction or clinical outcomes. Use fictional customer information only.

## Open the app locally

Use Python **3.12**. Download/extract the project or clone its GitHub repository, then open a terminal in the folder containing `app.py`:

```sh
pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a local link, normally [http://localhost:8501](http://localhost:8501). Open that link in your browser. Keep the terminal running; press Ctrl+C to stop the app. If port 8501 is occupied, use `streamlit run app.py --server.port 8502` and open the printed URL.

An optional isolated environment:

```sh
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in Windows PowerShell or `source .venv/bin/activate` on macOS/Linux, then run the installation and launch commands above. If command shortcuts are unavailable, use `python -m pip install -r requirements.txt` and `python -m streamlit run app.py`.

## Five-minute walkthrough

1. **Hypotheses:** see each hypothesis's suggested next step, choose one, and read its **Current thesis**. Open **Why this recommendation?** for the rules and cited evidence. **Review recommendation** opens an editable decision draft; it saves nothing automatically. The evidence table separates Says, Does, and Research into supports, contradicts, and unclear counts.
2. **Evidence → Add a source — upload or paste:** paste an interview or upload `data/sample_interview.txt`. Click **Extract document for review**, preview the text, set metadata, and click **Add evidence**. DOCX paragraphs/tables and PDF page locations are retained. Choose a source category (initial interview, follow-up interview, customer feedback review, observed behavior, or external research). External research requires its original URL. Dates have defaults; context and limitations are optional notes.
3. **Evidence:** your saved source is selected automatically. Under **Link to a hypothesis**, choose its passage and hypothesis, select a position, and explain it. The passage supplies the quotation automatically; **Use a shorter excerpt** is optional. Save the proposed link. Alternatively, **AI suggestions** proposes passage types and hypothesis links with exact quotations filled in. Uploaded passages are preselected up to the request limit; proposals remain pending until reviewed.
4. **Review suggested links:** inspect the quotation against the source. Edit the position, rationale, or quotation as needed, enter your name, select Approved/Pending/Rejected, and save. Only approved, current-revision links enter triangulation.
5. **Edit evidence:** change a source passage. The original text remains in revision history, and its classifications become **Needs review**. Approving them again requires a quotation that matches the new source. Hypothesis wording edits similarly create a new version and require re-review.
6. **Contradictions:** inspect the bundled DEMO-001 and DEMO-006 intention/action mismatches. Read both sources, then confirm or dismiss the mismatch with an explanation. This does not change any strategic decision.
7. **Decisions:** log a product/offer/ICP change and select affected hypotheses. Older evidence is flagged for revalidation. Your decision with a rationale, reviewed assessment references, and the next test.
8. **Project → Export project:** download your complete project JSON. Restore it later with **Import project**.

No account or API key is needed for this walkthrough. Bundled example classifications are explicitly labeled authored demo examples, not live AI output.

## What is included

- **Hypotheses:** six initial pain hypotheses, support/contradiction/unclear views, source traceability, version history, review dates, and human decision history.
- **Evidence:** add, upload, edit, archive, restore, search, and sort sources; exact-citation validation; classification review history; freshness review; optional AI proposals.
- **Customers:** manual addition/editing, CSV preview and import, dated action records, segment/channel/cohort filters, and editable power-user scoring.
- **Contradictions:** deterministic candidate detection with source pairs, reviewer explanations, and revision-specific review history.
- **Decisions:** review deadlines, product/ICP change history, scoped context flags, decisions with evidence snapshots, and next experiments.

The initial cohorts are customers 1–10, 11–30, and 31–100; additional customers belong to 101+. Comparison customer segments intentionally extend beyond the initial ICP. Patterns are synthetic illustrations, not inferred market findings.

## Interpretation rules

**Current thesis:** a transparent rule-based draft summarizes reviewed evidence for the selected customer group. This works without an API key and is not presented as live AI inference. Only current, approved customer evidence contributes to directional recommendations. Research remains context. Customers are counted once per direction; customers with mixed findings are kept separate.

The draft can recommend considering doubling down or retirement only with at least five distinct customers on the corresponding side, across at least two acquisition cohorts, including two customers with aligned Says and Does links, and a directional balance of at least 2:1. Mixed findings or unresolved mismatches block those recommendations. Review-due sources or an overdue hypothesis review instead produce **Revalidate first**. Weaker patterns lead to further testing, investigation, or a narrower hypothesis. These are conservative product review rules, not validated statistical thresholds. Evidence counts do not establish a clinical outcome or population-wide claim.

**Review recommendation** takes the draft, evidence references, and next test into Decisions. The reviewer can change the action and wording and must provide their name before saving. The saved decision retains the recommendation snapshot alongside evidence snapshots. Nothing retires a hypothesis or changes the strategic decision automatically.

The interface uses one **Demo data** notice, simpler navigation labels, a larger thesis panel, and short opacity/hover transitions. Reduced-motion preferences disable animation. Source text, exported provenance, and original review records remain intact even where repeated demo boilerplate is omitted from display copy.

**Triangulation:** count distinct source records per position, not repeated quotations. One source can contain mixed findings. A hypothesis detail also shows distinct customer count. Sources are not independent votes; research population/context remains visible. Multiple files from one interview/study should be kept as one source, rather than counted as separate studies. No statistical confidence is computed.

**Contradictions:** the app detects two types of candidates:

- A reviewer-confirmed customer intention with an exact quote, action, and deadline differs from the action record after observations cover that deadline. Unknown and Not applicable actions are excluded. A late completion is flagged as late, not treated as never completed.
- Approved Says and Does assessments take opposite positions on the same hypothesis for the same customer, within 90 days and the same product/ICP context version.

These rules do not discover every semantic contradiction and do not establish causation. A missed action can reflect affordability, availability, changed needs, or appropriate non-use. A contradiction review applies to specific source revisions; editing a source causes the new candidate to require review again. Historical reviews remain in the project export.

**Freshness:** source/publication date is separate from review date. Review due means a configured deadline passed, not that a finding became false. Context changed means a relevant logged change postdates the source's context version. Unlinked sources are conservatively flagged after context changes until their relevance is reviewed. Historical evidence remains visible. In Evidence, use **Freshness** to record applicability, reviewer, rationale, and the next review date. Reapprove classifications after the new source revision. Recording a decision alone never silently refreshes sources.

**Power users:** default weights are Baseline purchase +1, blood draw and results delivered +2, results reviewed +2, next steps viewed +1, consultation booked +2, and follow-up test completed +2. The illustrative cutoff is 7. Count each completed action once within 30 days of purchase. The score is an engagement signal; the deck calls for separate checks of appropriate return use and reported value. Score controls are exploratory session settings and are not part of strategic decisions or project exports.

**Return rates:** denominators include only customers with a full 30/90-day observation window and a known, applicable result. Both windows use the first meaningful return date. Unknown or Not applicable outcomes are excluded, not converted to failure. Sample size and eligibility are displayed. A newly added customer starts with unknown follow-up outcomes.

## Customer CSV

Use `synthetic_customers.csv` or **Customers → Upload CSV → Download customer CSV template**. This dated schema replaces the earlier dashboard's boolean-only CSV.

Required base columns: `id`, `number`, `age`, `segment`, `channel`, `trigger`, `discount`, `satisfaction`, `purchased_on`, `observed_through`, `note`.

Each of the following also needs a matching `_date` column:

```text
baseline_purchased
baseline_completed
results_reviewed
next_steps_viewed
consultation_booked
follow_up_test_completed
return_30_day
return_90_day
successful_referral
```

Status values: `Completed`, `Not completed`, `Unknown`, `Not applicable`. Completed actions require an ISO `YYYY-MM-DD` date; other statuses require an empty date. Customer ID and acquisition number must be unique. Purchase must be completed. Observation end cannot precede purchase or be in the future. Event dates must fall in the observation period. Discount is 0–100; satisfaction is 1–5; age is 18–100.

CSV import previews before applying. **Reject duplicates** prevents accidental updates. **Update matching IDs** explicitly replaces matching customer records and revises their behavioral sources. Customers omitted from an import remain in the project, preserving linked evidence. Invalid files leave current data intact. For a complete project replacement use project JSON import. Limits: 1,000 customers per CSV, 5 MB CSV/document, 10 MB project JSON, 80 PDF pages, 150,000 extracted characters per source.

## Present without an API account

Open **AI analysis → Demo scenarios → Analyze workspace**. This mode uses bundled prepared response templates and calculated source counts. It does **not** call a model or the network. All results are labeled simulated.

Under **Try a demo input**, choose a support, pivot, or challenge scenario. Download its interview TXT, upload it in Evidence, choose Initial interview or Follow-up interview, and save it. Alternatively, download the customer update CSV and apply it in Customers with **Update matching IDs**. You can paste the exact sample paragraph into a customer note or evidence passage. Run analysis again, or enable automatic updates. New classifications are Pending, citations point to your saved passage, and the prepared findings change accordingly. No strategic decision is saved.

Scenario matching requires the exact prepared paragraph and the original hypothesis statement. Unmatched text is deliberately left unclassified; it is not guessed or presented as genuine AI reasoning. Templates live in `data/demo_ai_scenarios.json`. The scenario CSV updates the first existing customer; use the ordinary customer template for other records. Export your project if you want to preserve demo changes.

## Real local AI with Ollama

Install [Ollama for Windows](https://docs.ollama.com/windows), then in PowerShell run:

```powershell
ollama pull qwen3:0.6b
```

The installed starter model is intentionally small for a quick local demonstration; it is not a quality benchmark. You can later run `ollama pull qwen3:4b` and change Local model to `qwen3:4b` for a larger model.

Keep Ollama running. Its local API normally listens on port 11434. Start Streamlit, choose **AI setup → Local Ollama**, keep the model name `qwen3:0.6b`, and click **Check Ollama**. Then open **AI analysis → Local Ollama**, select 1–3 sources, and click **Analyze workspace**. This runs a real model on your PC without an API account. It may take several minutes. There is no cloud fallback and automatic refresh is disabled in local mode to avoid repeated long runs.

Local mode defaults to classifying selected active sources. **Analyze all sources and customer notes** includes the entire customer base and active evidence, with a longer runtime. It also produces workspace findings from existing current links, sampling at most two recent links per position per hypothesis/segment and limiting each synthesis excerpt to 1,400 characters. Sampling is disclosed in findings; this is not an exhaustive review. The app attaches the exact full input passage to local classifications, checks all IDs and validates structured output before committing changes. Invalid or incomplete responses leave the previous project intact. A small local model can still misunderstand evidence: keep the human review step.

Streamlit calls `http://127.0.0.1:11434` from its Python server, not from the visitor's browser. This works when Streamlit and Ollama run on the same PC. **Streamlit Community Cloud cannot reach Ollama on your laptop.** Use Demo scenarios for a public cloud presentation, or the optional OpenAI provider. No additional Python dependencies are required for Ollama.

## Automated workspace analysis

1. For cloud inference, choose **OpenAI**, connect your key in **AI setup**, then open **AI analysis**. Demo and local alternatives are described above.
2. Enable **Send workspace data to OpenAI for analysis**, then click **Analyze workspace**. The app processes all active sources and customer records together, including customer CSV notes as citable Says sources and recorded actions as Does sources. One customer can have evidence for multiple hypotheses; membership in a segment is not automatically support.
3. AI proposes hypothesis links and writes draft conclusions for Dashboard, Hypotheses, Customers, Evidence, Contradictions, and Decisions. Each finding cites exact stored assessment IDs, quotations, review status and source revision. Findings use the whole project, independently of exploratory page filters. Segment calculations use default score weights and cutoff 7; return denominators exclude unknown and immature windows.
4. Enable **Automatically update after saved data changes** to refresh findings after saving an interview, applying a CSV, editing a hypothesis, or reviewing evidence. This authorizes sending subsequent saved project inputs while the session is open. Uploads must first be saved/applied. Disable the setting or the send checkbox to stop automation. Navigation alone causes no API calls.
5. **Review proposed links** opens the existing approval workflow. You do not need to approve each link before reading AI findings, but unreviewed drafts are labeled, and only approved links can be cited in a saved human decision. The original rule-based Current thesis remains separately available and uses reviewed evidence only.

The first run batches the workspace; later runs analyze only changed sources and refresh the combined conclusions. Changed input fingerprints label older findings out of date. A failed run retains the prior project and report, pauses automatic retry for those inputs, and offers an explicit retry. AI never approves evidence, changes a human decision, or retires a hypothesis. Research stays research. Claims still require human judgment: exact-citation checks establish traceability, not truth.

Workspace analysis sends active source passages, customer attributes/notes, hypotheses/ICP, linked classifications and aggregate usage metrics to OpenAI. Original files and API keys are not included in the payload. It allows at most 40 source batches (about 24,000 serialized characters each), 14,000 output tokens per batch, and one synthesis request (up to 700,000 serialized input characters and 12,000 output tokens). Each call has a 60-second timeout and no automatic retries. A first run can take several minutes and incur multiple API charges. Oversized projects stop explicitly; they are not silently truncated. A provider context/output limit may require smaller inputs or another compatible model. Reports and citation snapshots persist in project exports; automation consent and credentials do not.

## Optional live AI

The app includes an OpenAI Responses API integration using [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs). It uses no agents, vector database, autonomous research, or scheduled worker. Optional automatic refresh runs synchronously after saved changes in the open session.

For an interactive setup, open **AI setup** in the sidebar. Create an API key through the linked [OpenAI dashboard](https://platform.openai.com/api-keys), enter it in the masked field with a model ID, and click **Use key for this session**. This stores the key only in server session memory, clears the input, and makes no API request. On a hosted app, the server receives the key; use only a trusted deployment. It is never included in project JSON, CSV, or written to disk by the app. **Remove session key** clears this override (a configured server key may still apply). Reloading or resetting the session also clears it.

**Test API connection** explicitly checks model access, sending no evidence. It does not guarantee generation access, quota or successful structured output. Then choose **Go to Evidence**, open **AI suggestions**, select passages, confirm sending, and analyze. The [official OpenAI quickstart](https://developers.openai.com/api/docs/quickstart) explains API-key creation and server-side configuration. No real credential or billed inference was used during development; setup and failure paths are tested with mocks.

For a persistent deployment, copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml` locally, or configure these values in Streamlit Community Cloud's Secrets settings:

```toml
ENABLE_LIVE_AI = "true"
OPENAI_API_KEY = "your-server-side-key"
OPENAI_MODEL = "gpt-4o-mini"
```

Choose a Responses API model supporting structured outputs that your account can access. Never commit an API key; `.streamlit/secrets.toml` is gitignored. Environment variables with the same names also work. Restart the local app after changing configuration.

Under **Evidence → AI suggestions**, select passages, check the explicit send checkbox, and click **Analyze selected evidence**. Only the selected text, source category/context/date/type, working ICP, and hypotheses are sent to OpenAI. Original document binaries, full customer tables, and unrelated sources are not sent. Model ID, prompt version, creation time, original proposal, and human edits are recorded. AI also proposes Says, Does, or Research for each linked passage. Self-reported actions are Says, not observed Does evidence. External research remains Research even when it quotes study participants. A reviewer can correct passage types before approval. Every quote is checked against source text before proposals are saved. A failed or refused request leaves manual review available and changes no decisions.

Individual-passage requests are limited to 24,000 source characters and 3,000 output tokens, with a 45-second timeout, no automatic retries, and 10 attempts per session. Session limits are convenience controls, **not** account-wide cost protection. An unauthenticated public app can be opened in new sessions. Leave live AI disabled for a freely accessible demo; enable it only with deliberate provider usage controls and a limited audience. Hosting and API billing are separate.

The live API path has been tested with a mocked provider response and invalid-citation cases. No credential was configured during development, so a real billed inference has **not** been verified.

## Deploy from GitHub to Streamlit Community Cloud

1. Create a GitHub repository. Upload the application package preserving directories: `app.py`, `evidence.py`, `analysis_tools.py`, `analytics.py`, `requirements.txt`, `README.md`, `.gitignore`, `synthetic_customers.csv`, `.streamlit/`, `data/`, `scripts/`, and `tests/`. Do not upload `.venv`, credentials, or unrelated case/deck files.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub. Choose **Create app**, select your repository and branch, and set the entrypoint to `app.py`.
3. Select **Python 3.12** in advanced settings. No secrets are required for the demo. Deploy and wait for dependency installation.
4. Open the generated `*.streamlit.app` link and share it. Visitors only need that link and a browser; they do not install Python or sign in to use a public demo.
5. Commit changes to the selected branch to update the app. Configure optional AI secrets in the Cloud UI, never in a committed file.

Follow the official [deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). This repository is ready for deployment; creating a GitHub repository or publishing a hosted app is a separate step and has not been performed here.

## Storage and limits

All edits live in the current Streamlit session. Refreshing, disconnecting, restarting the server, or a sleeping cloud app may reset them. **Export your project before leaving.** Imports validate references and approved quotations before replacing the active project. Export preserves extracted source text, locations, revisions, decisions, and review history; it does not preserve the original uploaded binary. Keep originals separately if needed.

Each visitor has an independent project. There is no database, authentication, shared editing, or scheduled monitoring. Reviewer names are self-entered and history is an editable project record, not a tamper-proof audit system. Scanned PDF OCR, audio transcription, charts of invented confidence, automated research retrieval, clinical advice, and production handling of identifiable customer data are outside v1.

## Development and checks

```sh
python -m unittest discover -s tests -v
```

Tests cover source edits and review invalidation, deduplicated source counts, exact citations, hypothesis versions, contradiction eligibility, scoped freshness, invalid imports, customer updates, project round-trip, document extraction, the mocked AI contract, and Streamlit interactive flows.

`evidence.py` holds the small validated data model and rules. `analytics.py` calculates activity metrics. `analysis_tools.py` handles document extraction and optional AI. `ai_workspace.py` handles incremental batch analysis and workspace synthesis. `local_ai.py` provides prepared demo outputs and loopback-only Ollama calls. `app.py` contains the UI. No backend service is needed. Recreate the bundled synthetic project with `python scripts/generate_demo.py` (this overwrites bundled demo data and the sample CSV). See [data/README.md](data/README.md) for research sources and limitations.

### Demo stories and appearance

Navigation is in the sidebar. Cohorts sort numerically: 1–10, 11–30, 31–100, then 101+. “Older professional” and “Family coordinator” are segments outside the original ICP, previously labeled “/ comparison”; the suffix has been removed.

The default palette is dark green. Use the top-right **⋮ → Theme** to choose the bundled Light or Dark palette. Streamlit remembers appearance in the browser.

Start with **H3** for a double-down example, **H4** for a segment-specific pivot, and **H5** for a retirement example. Expand **Why this recommendation?** for segment counts and source citations. The newer multi-paragraph interviews and observed task records provide paired Says/Does evidence. H1/H2/H6 retain revalidation cases. Recommendations remain rule-based drafts; “Consider a pivot” becomes an editable **Revise** decision. See [data/README.md](data/README.md) for scenario design and review dates. Reset the bundled demo from the sidebar Project section to load new scenarios into an existing session; export any work first.

### Review history and navigation

Main content remains centered when the sidebar opens. The sidebar overlays the page with a softened background; use its top close control to return to the page. It starts collapsed.

**Evidence → Recent reviews** shows the latest 25 classification reviews across all sources, regardless of library filters. **Review history** below a selected link shows its complete audit as readable rows, newest first, including reviewer, UTC time, outcome, position and rationale. The just-reviewed link remains selected and its history opens after saving. Original proposals and full before/after records remain available under the audit expander and in project exports.

### Dashboard and filters

**Dashboard** is the landing page: DAU, rolling 30-day MAU, prior-window growth, inactivity churn, active retention, new paid customers, event counts and daily/monthly charts. The fixed activity snapshot covers 1 March–20 September 2026. Use **Dashboard filters** for segment, acquisition channel, cohort, as-of date and timeline length. This is business usage, not infrastructure uptime. No real visitor tracking runs.

An active user has at least one app-open, results-open, care-plan-view or booking-view event. Multiple events from one customer count once per day/window. Rolling MAU covers the selected day and previous 29 days; growth compares the preceding non-overlapping 30 days. Inactivity churn is previous-window active customers absent from the current window divided by previous-window active customers. Retention uses the same denominator. Zero-denominator or incomplete-window rates show a dash. Calendar-month charts label incomplete months and do not use them for growth comparisons. Clinical action completion and usage events are separate. Activity is exported/restored with the project. Existing projects without activity show **Load demo activity**, which adds events only for matching demo customer IDs and preserves evidence, reviews and decisions.

**Evidence:** text search and a single sort selector: newest/oldest added, newest/oldest source date, most passages, or source ID. Addition order follows the stored project list, including for older imports without timestamps; editing an existing record does not move it. Archived records are available in a separate collapsed section. **Hypothesis filters:** text search, recommendation, human decision and segment/channel/cohort. Customer filters recalculate the thesis while retaining external research; text/recommendation filters select hypotheses without hiding their counterevidence. **Customer filters:** existing segment/channel/cohort plus search, power-user status, score, age, satisfaction and 30-day return eligibility. Empty selections mean all; clear individual selections to reset.

All 24 bundled interviews now have three passages. Choose **Sort evidence → Most passages** to find longer interviews quickly. The source selector shows passage counts, and **Read all 3 passages** displays the complete interview together. Twelve longer interviews have separately approved links to multiple hypotheses; new context paragraphs in the early twelve remain unclassified. Existing sessions keep their saved evidence; the longer interviews I-013–I-036 are already present in the earlier demo. Reset only if you want the refreshed early interviews, after exporting your work.

Evidence and customers default to **Newest added**. Source date and purchase date are separate sort options, so importing an old interview today still puts it at the top of newest additions. Customer search, segment, channel, cohort and engagement controls all live in the **Filters** toolbar panel. Sorting applies to both the table and record selector; the currently selected record may remain selected while browsing.

### Customer tools and review-to-decision workflow

Customers has a single toolbar: **Add / edit**, **Upload CSV**, **Scoring**, and **Filters**. Each icon has a text label and opens a popover; click outside to close it. Scoring and filters stay applied when their panels close.

To use evidence in a decision: read the source, propose a hypothesis link manually or with AI, then use **Review suggested links**. **Compare with the source** places the original passage beside the proposed quotation. Confirm the position and rationale, enter your name, select Approved/Pending/Rejected and save. Approval validates the evidence-to-hypothesis link, not the hypothesis itself, and does not reset freshness. **Use this evidence in a decision** opens Decisions with that citation selected. Preview its quotation, reviewer and freshness, add your reasoning and next test, then explicitly save the decision. Only approved links with valid current source and hypothesis revisions are available to cite. **Review waiting evidence** returns to a source needing review.

**Log a product / ICP change** records a changed product/service, target customer, price/offer or other context. Its placeholder gives product-version and ICP examples and asks which earlier findings might no longer apply. Select affected hypotheses to flag their earlier evidence for revalidation. This is distinct from reviewing a source or approving a classification.

## Local verification on this PC

Ollama 0.34.2 and Qwen3 0.6B were installed and tested through the loopback API and the Streamlit interface. A warmed selected-source run produced 13 workspace findings in approximately 11 seconds; the first model load took about 30 seconds on this machine. Browser testing on I-013 produced two new pending links. This is a functional integration check, not a model-quality evaluation. The model incorrectly classified an explicit affordability example, so prepared Demo scenarios are the more predictable presentation path. Full-workspace local inference was not benchmarked. No live OpenAI calls were used.


### Finding the analysis output
After **AI analysis > Analyze workspace**, the result appears under **Preliminary findings**, above the run controls. Choose a Summary section to read that part of the report. Each workspace page also shows an open **AI summary** at the top; Hypotheses and Customers let you choose the summary target. Expand **Evidence & next test** for quotations, review status, limitations, and a direct review link.

Demo summaries are prepared narratives filled with current segment metrics, reviewed hypothesis rules, freshness and mismatch counts. They state preliminary findings rather than just next steps. They are not live LLM outputs. For example, the bundled current evidence suggests considering doubling down on H3, pivoting H4, and retiring H5; edits and freshness reviews can change these directions. Unreviewed scenario links are separately identified and do not change approved-evidence recommendations. Rerun analysis after edits, or enable automatic updates. Old prepared reports upgrade once without calling an API. Final decisions remain manual.


### Ask your data
Open **Ask your data** in the sidebar for a read-only analysis workbench.

- Choose Evidence comparison, Daily active users, Monthly active users, or Customer segments.
- Set segments and dates. For evidence, select Says / Does / Research, hypotheses, review status and freshness. Does + Research is the default, so interviews are excluded. External research with no linked customer remains available as context. Only existing hypothesis links are analyzed; this page does not classify unlinked text.
- Ask a question, then click **Run analysis**. In **AI setup**, select Local Ollama for an AI-written response without an API account. OpenAI is optional and requires separate consent for the selected data. Demo mode calculates the chosen results and charts but does not interpret arbitrary questions.
- Read the answer, inspect cited data, and download the data CSV or analysis JSON. Chart menus support image download. Scope, question or project changes require a new run; old results are hidden until refreshed. This workbench never approves evidence or records decisions.

Example: choose Evidence comparison, keep Does and Research, select H3, and ask “What supports this hypothesis without interview evidence, and what remains unknown?” Or select Daily active users, choose a segment/date range, and ask “Where did activity change, and what should we investigate?” The chart is calculated directly from activity records; the model cannot execute code or change its values.

Evidence dates refer to source dates; customer comparison dates refer to purchase dates. Daily active users are unique customers per day, and monthly active users are unique customers per calendar month. Partial boundary months are labeled in the table. Segment scoring uses default weights and cutoff 7. Model interpretation receives at most the first 40 matching rows (1,200 characters per quotation), plus full-selection calculated facts; use narrower scopes for focused answers. The UI discloses sampling. Unknown model citations are rejected, but valid citations do not guarantee a correct interpretation. Results are session-local; use the downloads to keep them.

Ask your data results include an open **AI summary** above the chart. In demo mode, a labeled calculated template explains evidence balance, activity changes or segment differences for the selected scope. With a connected model, this section shows its answer to your question. Expand **Evidence & calculation details** to inspect the basis. Download analysis includes the displayed summary and its origin.
