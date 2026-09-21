"""Recreate the fictional demo. Run from the repository root."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import date, timedelta
import json
import random
from evidence import (ACTIONS, ROOT, Customer, Event, Hypothesis, Project, Source,
                      add_assessment, behavior_source, customer_frame, review_assessment)

rng = random.Random(20260921)
titles = ["No trusted starting point", "Disrupted health routines", "Wellness without clarity",
          "Motivation without direction", "A personal health concern", "Care takes too much time"]
statements = [
    "Young professionals experience uncertainty about where to turn because they lack a regular doctor or have limited HMO support.",
    "Young professionals have difficulty maintaining healthy habits because desk work and commuting reshape their daily schedule.",
    "Young professionals feel uncertain about health progress because fitness habits alone do not explain their underlying health.",
    "Young professionals have difficulty choosing what to change because willingness to act outpaces personalized health guidance.",
    "Young professionals worry about future health risks because a flagged result or family history raises unanswered questions.",
    "Young professionals delay tests and follow-ups because separate visits compete with work and other commitments.",
]
hypotheses = [Hypothesis(id=f"H{i}", title=t, statement=s, origin="Alaga pitch deck v10, slide 4 (faithful transcription).", review_on=date(2026,10,1)) for i,(t,s) in enumerate(zip(titles, statements),1)]
customers = []
segments = ["Young professional / health concern", "Young professional / wellness", "Young professional / time pressure", "Older professional", "Family coordinator"]
for i in range(1,101):
    group = rng.choices(range(3), [30,20,20])[0] if i<=12 else rng.choices(range(5), [30,20,20,20,10])[0]
    start = date(2026,3,1) + timedelta(days=i)
    end = start + timedelta(days=100)
    engaged = rng.random() < [0.8,0.45,0.65,0.8,0.6][group]
    events = {a: Event(status="Not completed") for a in ACTIONS}
    events["baseline_purchased"] = Event(status="Completed", on=start)
    for action, day in [("baseline_completed",7),("results_reviewed",8),("next_steps_viewed",9),("consultation_booked",14),("follow_up_test_completed",27)]:
        if rng.random() < (0.92 if action == "baseline_completed" else 0.85 if engaged else 0.25):
            events[action] = Event(status="Completed", on=start + timedelta(days=day))
    if events["baseline_completed"].status != "Completed":
        for action in ["results_reviewed", "next_steps_viewed", "follow_up_test_completed"]:
            events[action] = Event(status="Not completed")
    if engaged and rng.random() < 0.65:
        events["return_30_day"] = Event(status="Completed", on=start + timedelta(days=20))
        events["return_90_day"] = Event(status="Completed", on=start + timedelta(days=20))
    elif engaged:
        events["return_90_day"] = Event(status="Completed", on=start + timedelta(days=55))
    if engaged and rng.random() < 0.3:
        events["successful_referral"] = Event(status="Completed", on=start + timedelta(days=40))
    if i in [1,6]:
        events["consultation_booked"] = Event(status="Not completed")
    if i % 13 == 0:
        events["follow_up_test_completed"] = Event(status="Not applicable")
    customers.append(Customer(id=f"DEMO-{i:03d}", number=i, age=rng.randint(22,34) if group<3 else rng.randint(38,56),
        segment=segments[group], channel=rng.choice(["Personal outreach","Workplace community","Fitness community","Referral","Paid social"]),
        trigger=rng.choice(["Flagged prior result","Family history concern","Wanted clear next steps","Convenient booking"]),
        discount=rng.choice([0,0,10,20]), satisfaction=rng.choice([3,4,5]) if engaged else rng.choice([2,3,4]),
        purchased_on=start, observed_through=end, note="Fictional customer generated for the Alaga learning demo.", events=events))

p = Project(customers=customers, hypotheses=hypotheses, sources=[behavior_source(c,1) for c in customers])
quotes = [
    ("H1", "Supports", "I do not have a regular doctor and did not know where to start. I plan to book a consultation by the end of this month."),
    ("H1", "Contradicts", "My regular doctor already explains my results. I bought this for convenience, not because I lacked a trusted starting point."),
    ("H2", "Supports", "Since starting a desk job, my commute leaves me no time for my usual exercise routine."),
    ("H2", "Contradicts", "My work schedule is flexible and my exercise routine has stayed consistent. Work is not my main health barrier."),
    ("H3", "Supports", "I go to the gym but still cannot tell whether my health is improving. Fitness alone has not answered my questions."),
    ("H6", "Supports", "Separate visits compete with my work schedule, so I keep delaying follow-up. I plan to book a consultation by the end of this month."),
    ("H3", "Contradicts", "My existing care team and fitness plan already give me a clear picture. I only wanted easier access to the test."),
    ("H4", "Supports", "I am ready to change my habits, but I do not know which next step matters most for me."),
    ("H4", "Contradicts", "I know exactly which changes my doctor recommended. The difficulty is paying for them, not choosing a direction."),
    ("H5", "Supports", "A flagged result and my family history worried me. I paid because I had unanswered questions about my risk."),
    ("H5", "Contradicts", "I had no flagged result or family concern. I tried the service because a friend offered a discount."),
    ("H6", "Contradicts", "Separate appointments fit my flexible schedule. Cost is the reason I have postponed care, not time."),
]
for i,(hid,stance,text) in enumerate(quotes,1):
    c = customers[i-1]
    on = c.purchased_on + timedelta(days=10)
    s = Source(id=f"I-{i:03d}", title=f"Fictional interview {c.id}", kind="Says", customer_id=c.id,
        chunks={"Interview paragraph 1": text}, source_date=on, review_on=on+timedelta(days=180),
        context="Fictional buyer interview. Single self-report; not representative. No real person was interviewed.")
    if i in (1,6):
        s.expected_action = "consultation_booked"
        s.expected_by = date(2026,3,31)
        s.expectation_quote = "I plan to book a consultation by the end of this month."
        s.expectation_reviewer = "Demo reviewer (fictional)"
    p.sources.append(s)
    a = add_assessment(p,s.id,hid,"Interview paragraph 1",text,stance,
        "The fictional customer directly describes " + ("the proposed problem." if stance == "Supports" else "a different experience or purchase motivation."),
        "One synthetic interview. Do not generalize to the target population.", "Bundled example; not live AI")
    if i <= 10:
        review_assessment(p,a.id,a.stance,a.quote,a.chunk,a.rationale,a.limitations,"Approved","Demo reviewer (fictional)")

research = [
    dict(id="R-001",title="WHO: physical activity",date="2024-06-26",
         url="https://www.who.int/news-room/fact-sheets/detail/physical-activity",
         text="WHO reports that 31% of adults globally do not meet recommended physical activity levels. Its fact sheet describes increasingly sedentary lives associated with motorized transport and screen use at work, in education, and in recreation.",
         context="Publisher: WHO. Global fact sheet, not a Philippine young-professional customer study. Does not establish that commuting causes this cohort's reported difficulties or that they will buy Alaga. Bundled text is an editorial paraphrase, not a verbatim extract.",hid="H2"),
    dict(id="R-002",title="Cochrane: general health checks",date="2019-01-30",
         url="https://www.cochrane.org/evidence/CD009009_general-health-checks-reducing-illness-and-mortality",
         text="A Cochrane review identified 17 randomized trials of general health checks; 15 reported results covering 251,891 participants. General health checks had little or no effect on all-cause mortality. The review searched for studies through 31 January 2018.",
         context="General adult screening, not an evaluation of Alaga or clinically indicated testing. Challenges equating more testing with health benefit; does not disprove a customer's desire for clarity. Bundled text is an editorial paraphrase, not a verbatim extract.",hid="H3"),
    dict(id="R-003",title="Malijan et al.: diabetes care access in Manila",date="2024-01-23",
         url="https://journals.plos.org/globalpublichealth/article?id=10.1371/journal.pgph.0002333",
         text="This mixed-methods study examined access to essential diabetes care in Manila during the COVID-19 pandemic. Patients and healthcare workers described disruptions to care, financial and transport barriers, and limits to telemedicine access.",
         context="PLOS Global Public Health; Malijan et al. Pandemic-era diabetes care. The clinical population and exceptional service conditions differ from the proposed Alaga ICP. Does not establish current demand or isolate work-related time pressure. Editorial paraphrase.",hid="H6"),
    dict(id="R-004",title="WHO: noncommunicable diseases",date="2025-09-25",
         url="https://www.who.int/news-room/fact-sheets/detail/noncommunicable-diseases",
         text="WHO describes noncommunicable diseases as arising from a combination of genetic, physiological, environmental, and behavioral factors. People across age groups are affected. Risk-factor management and accessible primary care are part of the response.",
         context="Global public-health context. Does not show that Alaga's target customers perceive risk, seek guidance, or will pay. Bundled text is an editorial paraphrase, not a verbatim extract.",hid="H5"),
]
for r in research:
    s = Source(id=r["id"],title=r["title"],kind="Research",chunks={"Bundled editorial summary":r["text"]},
        source_date=date.fromisoformat(r["date"]),review_on=date(2026,12,20),url=r["url"],context=r["context"]+" Source checked 2026-09-21.",synthetic=False)
    p.sources.append(s)
    a=add_assessment(p,s.id,r["hid"],"Bundled editorial summary",r["text"],"Unclear",
        "Relevant background, but the population and outcome do not directly test this customer hypothesis.",r["context"],"Bundled editorial example; not live AI")
    review_assessment(p,a.id,a.stance,a.quote,a.chunk,a.rationale,a.limitations,"Approved","Demo reviewer (example classification)")

# Seed a cautious behavioral assessment without claiming action proves customer value.
for i,hid in [(1,"H1"),(6,"H6"),(8,"H4")]:
    s = next(s for s in p.sources if s.id == f"B-DEMO-{i:03d}")
    quote = s.chunks["Customer action record"].split("\n")[0]
    a=add_assessment(p,s.id,hid,"Customer action record",quote,"Unclear",
        "Payment is observed in this fictional action record, but it does not establish the customer's reason for paying.",
        "Behavior requires interview context; engagement is not clinical value.","Bundled example; not live AI")
    review_assessment(p,a.id,a.stance,a.quote,a.chunk,a.rationale,a.limitations,"Approved","Demo reviewer (fictional)")

# Deliberately contrasting, dated teaching cases. These do not change real research.
# Keep H1/H2/H6 as stale or unresolved cases; enrich H3/H4/H5 with fresh evidence.
review_day = date(2026, 9, 20)
for h in p.hypotheses:
    if h.id in ("H3", "H4", "H5"):
        h.review_on = date(2027, 3, 20)
for source in p.sources:
    linked = {a.hypothesis_id for a in p.assessments if a.source_id == source.id}
    if linked.intersection({"H3", "H4", "H5"}):
        source.review_on = date(2027, 3, 20)
        source.context += " Teaching case: relevance reviewed on 2026-09-20; original collection date retained."

occupations = ["accountant", "designer", "software tester", "recruiter", "analyst", "project coordinator"]
settings = ["morning gym sessions", "weekend cycling", "a running club", "home strength training", "swimming", "dance classes"]

def approved_link(source, hid, chunk, stance, rationale):
    a = add_assessment(p, source.id, hid, chunk, source.chunks[chunk], stance, rationale,
        "Purposively selected teaching case. One customer is counted once per hypothesis; actions alone do not establish motivation or clinical benefit.",
        "Authored demo scenario; not live AI")
    review_assessment(p, a.id, a.stance, a.quote, a.chunk, a.rationale, a.limitations, "Approved", "Demo reviewer")

for j, n in enumerate([13, 14, 15, 31, 32, 33, 16, 17, 18, 34, 35, 36]):
    positive = j < 6
    k = j % 6
    c = customers[n-1]
    c.age = 24+k
    c.segment = "Young professional / wellness" if positive else "Young professional / time pressure"
    c.trigger = "Wanted clear next steps" if positive else "Convenient booking"
    c.discount = 0
    c.observed_through = review_day
    c.note = ("Maintained exercise habits but wanted an interpretable health baseline and a prioritized plan."
              if positive else "Had an established care plan; chose booking convenience over risk-focused guidance.")
    for action, day in [("baseline_completed",7),("results_reviewed",8),("next_steps_viewed",9),("consultation_booked",14)]:
        c.events[action] = Event(status="Completed",on=c.purchased_on+timedelta(days=day))
    if positive:
        c.events["follow_up_test_completed"] = Event(status="Completed",on=c.purchased_on+timedelta(days=27))
    else:
        c.events["follow_up_test_completed"] = Event(status="Not applicable")
    # Replace the generated behavioral record before adding any citations to it.
    original = next(x for x in p.sources if x.id == "B-"+c.id)
    p.sources[p.sources.index(original)] = behavior_source(c,1)
    if positive:
        chunks = {
            "Interview paragraph 1": f"I work as a {occupations[k]} and keep up {settings[k]}. I was still unsure what those habits meant for my health. That uncertainty, rather than a new symptom, is why I paid for the baseline.",
            "Interview paragraph 2": "I wanted to act but had a long list of conflicting suggestions. During the results review I asked which single change should come first. The ranked next steps gave me a starting point I could follow.",
            "Interview paragraph 3": f"I opened my results on day eight, read the next steps the following day and booked a consultation. I brought my questions about {settings[k]} to that appointment. The test by itself would not have resolved the uncertainty.",
        }
        observed = {
            "Observed session 1": "During the recorded results walkthrough, the customer compared their exercise log with the baseline report, could not explain the indicators and requested an interpretation session. The customer then opened results and booked the consultation shown in the action record.",
            "Observed session 2": "During the task walkthrough, the customer could not choose between three habit changes without help. After viewing the ranked next steps, they selected the first step and added it to their weekly plan.",
        }
        links = [("H3","Interview paragraph 1","Supports","Six wellness-oriented buyers distinguish activity from understandable health progress; interpretation is the recurring reason to pay."),
                 ("H4","Interview paragraph 2","Supports","This wellness customer needs prioritization despite willingness to act."),
                 ("H3","Interview paragraph 3","Supports","The follow-through makes the interpretation need concrete; it is not an additional independent customer.")]
        behavior_links = [("H3","Observed session 1","Supports","Observed difficulty interpreting indicators corroborates the interview; engagement alone would not establish this need."),
                          ("H4","Observed session 2","Supports","An observed prioritization task corroborates the reported difficulty choosing a next step.")]
    else:
        chunks = {
            "Interview paragraph 1": f"As a {occupations[k]}, I bought the baseline to fit a routine test around work. I had no flagged result or family-history worry driving this purchase. I already had a plan from my regular doctor.",
            "Interview paragraph 2": "I could tell you exactly which changes my doctor recommended before I used Alaga. I did not need another plan. A clear price and an appointment that fitted my calendar were what mattered.",
            "Interview paragraph 3": "I chose the routine-booking route when shown both that option and a risk-guidance package. I kept my existing plan and asked for the results to be shared with my doctor. I would pay for simpler coordination, not a new worry about future risks.",
        }
        observed = {
            "Observed session 1": "In a choice task with equal prices, the customer selected routine booking instead of the risk-guidance package, uploaded an existing routine test request and completed the booking. No risk-focused guidance was requested in the session.",
            "Observed session 2": "Before seeing Alaga next steps, the customer produced an existing clinician plan and correctly listed their next three actions. They skipped the planning exercise and completed scheduling and result-sharing tasks instead.",
        }
        links = [("H5","Interview paragraph 1","Contradicts","Convenience, rather than a flagged result or family concern, explains this customer's paid purchase."),
                 ("H4","Interview paragraph 2","Contradicts","Customers with an existing clinician plan need coordination, not help choosing a direction."),
                 ("H5","Interview paragraph 3","Contradicts","The package choice repeats the alternative motivation within the same interview; count this customer once.")]
        behavior_links = [("H5","Observed session 1","Contradicts","Equal-price package choice corroborates the reported convenience motive; it cannot establish the absence of every private concern."),
                          ("H4","Observed session 2","Contradicts","Independent task performance challenges the need for prioritization in customers with an existing plan.")]
    interview = Source(id=f"I-{n:03d}", title=f"{c.id} · {occupations[k]} follow-up", kind="Says",customer_id=c.id,
        chunks=chunks,source_date=review_day,review_on=date(2027,3,20),context="Follow-up interview with three separately cited paragraphs. Purposive sample across acquisition cohorts.")
    observation = Source(id=f"O-{n:03d}",title=f"{c.id} · observed service walkthrough",kind="Does",customer_id=c.id,
        chunks=observed,source_date=review_day,review_on=date(2027,3,20),context="Moderator observation notes from a structured service walkthrough. This task setting may affect behavior; not an independent customer.")
    p.sources.extend([interview,observation])
    for hid,chunk,stance,rationale in links:
        approved_link(interview,hid,chunk,stance,rationale)
    for hid,chunk,stance,rationale in behavior_links:
        approved_link(observation,hid,chunk,stance,rationale)

# Separate app-usage telemetry: observed coverage includes days with zero events.
from evidence import ActivityEvent
activity_rng=random.Random(812)
p.activity_start=date(2026,3,1)
p.activity_end=date(2026,9,20)
for offset in range((p.activity_end-p.activity_start).days+1):
    day=p.activity_start+timedelta(days=offset)
    for c in customers:
        if day<c.purchased_on:
            continue
        probability=.10 if day.month<7 else .16 if day.month==7 else .22 if day.month==8 else .25
        if day.weekday()>=5:
            probability *= .6
        if c.number%7==0 and day>=date(2026,8,22):
            probability=0  # A lapsed group; never equated with subscription cancellation.
        if c.number%11==0 and day<date(2026,9,1):
            probability=0  # Recently activated users.
        if activity_rng.random()<probability:
            p.activity_events.append(ActivityEvent(customer_id=c.id,on=day,activity="App opened"))
            if activity_rng.random()<.6:
                p.activity_events.append(ActivityEvent(customer_id=c.id,on=day,activity=activity_rng.choice(["Results opened","Care plan viewed","Booking viewed"])))

# Add depth to the early interviews without altering their originally cited passage.
for source in p.sources:
    if source.id in {f"I-{n:03d}" for n in range(1,13)}:
        n=int(source.id.split("-")[1])
        source.chunks["Interview paragraph 2"]=(
            "I compared the price with a nearby clinic before paying. I wanted the booking instructions and what would happen after results to be clear. I did not interpret buying a test as a promise that my health would improve."
            if n%2 else "I already had advice from a clinician. I checked the appointment times and whether I could send results back to that clinician. Convenient coordination mattered more than receiving another general checklist.")
        source.chunks["Interview paragraph 3"]=(
            "After opening the report, I wrote down two questions for my next appointment. Reading a report and understanding the next decision felt like different tasks. I would want someone to check that the advice fitted my situation."
            if n%3 else "My schedule changes each week. A reminder helps me remember an appointment, but it does not fix the price or travel time. I would prefer an evening slot and a clear estimate of the full cost.")

ROOT.joinpath("data").mkdir(exist_ok=True)
ROOT.joinpath("data/demo_project.json").write_text(Project.model_validate(p.model_dump()).model_dump_json(indent=2),encoding="utf-8")
ROOT.joinpath("data/external_research.json").write_text(json.dumps(research,indent=2),encoding="utf-8")
customer_frame(p.customers).to_csv(ROOT/"synthetic_customers.csv",index=False)
print(f"Created {len(p.customers)} customers, {len(p.sources)} sources, and {len(p.assessments)} assessments.")
