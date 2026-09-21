# Release verification

Prepared September 21, 2026, for interviewer review.

## Verified locally

- 52 automated tests pass using Python 3.12 and the pinned requirements.
- Browser checks on the running Streamlit app verified visible summaries, scoped evidence results, semantic chart colors, and sidebar navigation.
- Tests cover review history, classification invalidation, evidence freshness, contradiction rules, customer import, activity metrics, and scoped filtering.
- Ask your data excludes Says records when Does + Research is selected. Activity counts deduplicate customers by day. Changing the data or scope marks the displayed query result out of date.
- A real local Ollama request using qwen3:0.6b answered a scoped H3 question and returned valid source references. The model is small and can produce incorrect interpretations; this does not validate reasoning quality.
- Demo mode does not require an API account. Live OpenAI behavior uses mocked tests; no paid API call was made for release verification.
- The release archive is built from an explicit file list. API keys, secrets.toml, local environments, model downloads and personal session exports are excluded.

## Hosting checks still required

The app has not yet been verified on Streamlit Community Cloud. Account sign-in/terms acceptance and repository sharing must be completed before a live link can be certified for interviewers.

After deployment, verify the URL in a signed-out browser, run demo analysis, inspect Hypotheses and Ask your data, generate an activity chart, and test a source upload/review. Check public GitHub access separately. Free hosting may sleep between visits; open the app before the interview.
