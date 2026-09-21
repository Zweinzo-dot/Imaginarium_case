# Interviewer walkthrough

This repository contains Alaga Evidence Review, a working Streamlit prototype for testing early customer hypotheses. Customer records, interviews and actions are fictional. External research summaries cite their publications and are context only.

## Access

**Open [the live demo](https://alaga-evidence-review.streamlit.app/).** No login or installation is required. The [GitHub repository](https://github.com/Zweinzo-dot/Imaginarium_case) is public, and the complete source package is in [artifacts](artifacts/Alaga_Evidence_Review_MVP.zip). Localhost links only work on the computer running the local app.

You can run the full prototype now with Python 3.12:

```sh
pip install -r requirements.txt
streamlit run app.py
```

No account or API key is needed for demo mode. Each browser session has its own editable copy of the demo. Use Project > Export project before leaving to keep your edits; there is no database.

## Suggested ten-minute review

1. Open **Dashboard** for activity and retention metrics. The recorded activity ends on September 20, 2026; this is a historical demo, not live telemetry.
2. Open **AI analysis**, keep **Demo scenarios**, and click **Analyze workspace**. Then choose **Try a scenario > Run selected demo scenario**. Compare the clarity, affordability and workplace-trigger findings in **What changed in this demo**. Use the before/after table and **Review this scenario evidence** button to inspect the new pending link. Open **Overall workspace findings** to read **Preliminary findings**. These are labeled prepared interpretations of calculated metrics and reviewed evidence, not live model output.
3. In **Hypotheses**, inspect H3, H4 and H5. The seeded evidence illustrates support, mixed evidence and counterevidence. Check both sides and freshness before considering a direction. Recommendations can change as the data or review dates change.
4. Open **Ask your data**. Keep Does and Research to exclude interview evidence, run analysis, and read the summary above the chart. Blue means supports, red contradicts, and light blue unclear. Expand the underlying data and download the result.
5. Change Analyze to **Daily active users**, select a date range and run again. Counts are unique customers per day. Monthly charts distinguish partial from complete months in the data table.
6. In **Evidence**, upload `data/sample_interview.txt`, review the extracted passages, save the source, and add a hypothesis link. Approve or edit that classification with a reviewer name. Inspect review history.
7. In **Decisions**, record a human decision with approved evidence citations. Neither demo mode nor live AI saves strategic decisions automatically.

## AI capabilities and limits

- **Demo scenarios:** no network/model required. Exact bundled scenario passages produce prepared draft classifications. Summaries and charts update from the selected data. Arbitrary questions are not interpreted by demo mode.
- **Local Ollama:** live inference when the app and a downloaded model run on the same computer. A hosted Streamlit app cannot call the presenter's laptop localhost. The tested small model can misclassify evidence.
- **OpenAI:** optional account/key and explicit data-send consent. No shared API key is included. This path has mocked automated tests; a paid live API call was not used for release verification.

Ask your data uses bounded supplied rows for live interpretation, with sampling disclosed. Pandas computes the charts; models do not execute arbitrary code. Citations are validated against supplied IDs, but interpretation still requires review. Source text edits invalidate earlier classifications. Research and repeat quotations are not independent customer votes.

## Review the implementation

`app.py` contains the UI; `evidence.py` the data model and review rules; `analytics.py` activity calculations; `ai_workspace.py` batch analysis; `local_ai.py` demo/Ollama adapters; and `data_workbench.py` scoped queries and chart output.

Run `python -m unittest discover -s tests -q` for regression checks. See `VALIDATION.md` for what was verified and what remains to verify after hosting.
