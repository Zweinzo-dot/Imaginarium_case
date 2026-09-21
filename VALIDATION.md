# Release verification

Prepared September 21, 2026, for interviewer review.

## Verified locally

- 55 automated tests pass using Python 3.12 and the pinned requirements.
- Browser checks on the running Streamlit app verified visible summaries, scoped evidence results, semantic chart colors, and sidebar navigation.
- Tests cover review history, classification invalidation, evidence freshness, contradiction rules, customer import, activity metrics, and scoped filtering.
- Ask your data excludes Says records when Does + Research is selected. Activity counts deduplicate customers by day. Changing the data or scope marks the displayed query result out of date.
- A real local Ollama request using qwen3:0.6b answered a scoped H3 question and returned valid source references. The model is small and can produce incorrect interpretations; this does not validate reasoning quality.
- Demo mode does not require an API account. Live OpenAI behavior uses mocked tests; no paid API call was made for release verification.
- The release archive is built from an explicit file list. API keys, secrets.toml, local environments, model downloads and personal session exports are excluded.

## Hosted release checks

- Live URL: https://alaga-evidence-review.streamlit.app/
- Public repository: https://github.com/Zweinzo-dot/Imaginarium_case
- GitHub Actions installed the pinned dependencies on Linux/Python 3.12 and passed the regression suite: https://github.com/Zweinzo-dot/Imaginarium_case/actions/runs/35567305026
- Streamlit Cloud started successfully using Python 3.12.14. Its dependency setup replaced pyarrow 25 with 24 automatically.
- A fresh anonymous HTTP session received HTTP 200 for the app and an `ok` response from its health endpoint. No user credentials were supplied.
- Anonymous GitHub API/raw-file checks confirmed public visibility and access to source and the release ZIP; the ZIP matched the local release checksum.
- Browser checks on the hosted app verified dashboard activity metrics, demo workspace analysis and preliminary H3/H4/H5 findings, and Ask your data's filtered evidence summary and chart. Changing the query type correctly hid stale results until rerun. The daily-active-user query rendered 204 rows with its summary and chart. The sharing dialog confirmed Make this app public is enabled.

Live OpenAI calls and hosted local-Ollama inference were not tested. Ollama on a presenter's PC is not reachable from a Cloud deployment. Upload/review logic is covered by automated tests; a complete hosted upload/review/decision walkthrough was not repeated for this release. Free hosting may sleep between visits; open the app before the interview. Session edits require export to persist.

## Scenario runner update

The suite now includes three scenario-runner tests: all prepared classifications and distinct interpretations, repeat-run deduplication, preserved rejected reviews and edited source text, and the one-click Streamlit UI. All 55 tests passed locally before publication.
