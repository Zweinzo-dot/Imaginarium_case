# Bundled evidence

`demo_project.json` contains six v10 pain hypotheses, 100 fictional paid customers, 100 action records, 24 interviews, 12 observed walkthrough records, four external research summaries, and 79 classifications (77 approved, two pending). The authored scenarios are **not live AI output or real business validation**.

The current stories are dated 20 September 2026, with a review deadline of 20 March 2027; they will naturally become stale. H3 demonstrates **double down**: six wellness customers across two acquisition cohorts report uncertainty despite fitness habits, corroborated by observed interpretation tasks. H4 demonstrates **pivot / revise**: these buyers need prioritization, while six customers with existing care plans need coordination instead. H5 demonstrates **retire this broad purchase-motivation hypothesis**: six convenience-led buyers explicitly reject risk concern as their trigger and choose routine booking over equally priced risk guidance. An earlier supporting interview remains visible. H1, H2 and H6 retain stale evidence or unresolved contradictions for comparison.

The twelve new interviews each contain three separately cited paragraphs; each links to two hypotheses. Repeat paragraphs and observation notes from one customer never count as additional customers. The H3/H4/H5 older sources retain their collection dates and document a relevance review; research remains contextual and cannot vote a hypothesis into support. “Pivot” is stored as the existing **Revise** decision, preserving compatibility with exported projects.


`external_research.json` contains the same four research summaries as a small standalone reference dataset. These are short editorial paraphrases, not verbatim quotations or complete papers. In-app quotations from these entries cite the bundled paraphrase and link to the original publication. Imported research may instead contain exact original text with page/paragraph locations.

Sources checked 21 September 2026:

| Record | Original publication | Applicability limit |
| --- | --- | --- |
| R-001 | [WHO, Physical activity](https://www.who.int/news-room/fact-sheets/detail/physical-activity), 26 June 2024 | Global background; does not establish Philippine customer pain or willingness to pay. |
| R-002 | [Krogsbøll et al., Cochrane review of general health checks](https://www.cochrane.org/evidence/CD009009_general-health-checks-reducing-illness-and-mortality), 30 January 2019 | General screening differs from clinically indicated tests and Alaga's service. Does not directly test a customer's desire for clarity. |
| R-003 | [Malijan et al., diabetes care access in Manila](https://journals.plos.org/globalpublichealth/article?id=10.1371/journal.pgph.0002333), 23 January 2024 | Pandemic-era diabetes care differs from the initial young-professional ICP and current service conditions. |
| R-004 | [WHO, Noncommunicable diseases](https://www.who.int/news-room/fact-sheets/detail/noncommunicable-diseases), 25 September 2025 | Population health context cannot establish Alaga-specific purchase triggers or product value. |

All four research links are deliberately classified **Unclear** against the customer hypotheses. Topic relevance alone does not establish support. Reviewers can revise these interpretations with a documented rationale.

The seed generator uses fixed observation dates in 2026 and random seed 20260921. Dates are not moved forward on app launch; the sources naturally become due for review. `sample_interview.txt` is a small upload fixture. The app never contacts customers or retrieves linked research automatically.

Activity telemetry is bundled inside `demo_project.json` as `activity_events`, with explicit start/end coverage (2026-03-01 to 2026-09-20). Each entry is a fictional customer/date/activity event. Empty days within coverage are observed zero-activity days, not missing data. The seeded lapsed and returning groups illustrate growth and inactivity churn; they do not establish subscription cancellation. All 24 interviews now contain three paragraphs; original quoted passages and prior classifications are retained. Additional early-interview context remains unclassified for manual/AI review.
