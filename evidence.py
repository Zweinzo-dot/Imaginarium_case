"""Small, file-backed domain model. No server storage or external calls."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from typing import Literal
from uuid import uuid4

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path(__file__).parent
STANCES = ["Supports", "Contradicts", "Unclear"]
KINDS = ["Says", "Does", "Research"]
ACTIONS = {"baseline_purchased": 1, "baseline_completed": 2, "results_reviewed": 2,
           "next_steps_viewed": 1, "consultation_booked": 2, "follow_up_test_completed": 2,
           "return_30_day": 0, "return_90_day": 0, "successful_referral": 0}
EVENT_STATES = ["Completed", "Not completed", "Unknown", "Not applicable"]


def uid(prefix):
    return prefix + "-" + uuid4().hex[:10]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Event(Record):
    status: Literal["Completed", "Not completed", "Unknown", "Not applicable"] = "Unknown"
    on: date | None = None

    @model_validator(mode="after")
    def dated(self):
        if self.status == "Completed" and not self.on:
            raise ValueError("Completed actions require an event date.")
        if self.status != "Completed" and self.on:
            raise ValueError("Only completed actions have an event date.")
        return self


class Customer(Record):
    id: str = Field(min_length=1, max_length=80)
    number: int = Field(ge=1)
    age: int = Field(ge=18, le=100)
    segment: str = Field(min_length=1, max_length=120)
    channel: str = Field(min_length=1, max_length=120)
    trigger: str = Field(min_length=1, max_length=1000)
    discount: int = Field(ge=0, le=100)
    satisfaction: int = Field(ge=1, le=5)
    purchased_on: date
    observed_through: date
    note: str = Field(min_length=1, max_length=3000)
    events: dict[str, Event]

    @model_validator(mode="after")
    def dates(self):
        if set(self.events) != set(ACTIONS):
            raise ValueError("All nine action fields are required.")
        if self.observed_through < self.purchased_on or self.observed_through > date.today():
            raise ValueError("Observation end must be between purchase and today.")
        for action, event in self.events.items():
            if event.on and not self.purchased_on <= event.on <= self.observed_through:
                raise ValueError(f"{action}: event date must fall within the observation period.")
            if action in ("return_30_day", "return_90_day") and event.on:
                days = (event.on - self.purchased_on).days
                if not 0 < days <= int(action.split("_")[1]):
                    raise ValueError(f"{action}: return date is outside its window.")
        if self.events["baseline_purchased"].status != "Completed":
            raise ValueError("Customers must have a completed paid Baseline purchase.")
        if self.events["baseline_purchased"].on != self.purchased_on:
            raise ValueError("Baseline purchase date must equal purchased_on.")
        a, b = self.events["return_30_day"], self.events["return_90_day"]
        if a.status == "Completed" and (b.status != "Completed" or b.on != a.on):
            raise ValueError("A 30-day return must also be the first 90-day return.")
        if b.status == "Completed" and (b.on - self.purchased_on).days <= 30 and a.status != "Completed":
            raise ValueError("A return in the first 30 days must be recorded in both return fields.")
        return self


class Hypothesis(Record):
    id: str
    title: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    origin: str
    review_on: date
    history: list[dict] = Field(default_factory=list)


class Source(Record):
    category: str = "Other"
    id: str
    title: str = Field(min_length=1, max_length=200)
    kind: Literal["Says", "Does", "Research"]
    customer_id: str = ""
    # Chunks retain page/paragraph locations, including extracted document text.
    chunks: dict[str, str]
    source_date: date
    review_on: date
    url: str = ""
    context: str = Field(default="", max_length=3000)
    synthetic: bool = True
    revision: int = Field(default=1, ge=1)
    context_version: int = Field(default=1, ge=1)
    archived: bool = False
    history: list[dict] = Field(default_factory=list)
    expected_action: str = ""
    expected_by: date | None = None
    expectation_quote: str = ""
    expectation_reviewer: str = ""
    context_reviews: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def content(self):
        if not self.chunks or any(not k or not v.strip() for k, v in self.chunks.items()):
            raise ValueError("Evidence needs nonblank source text and locations.")
        if sum(map(len, self.chunks.values())) > 150_000:
            raise ValueError("Source exceeds 150,000 extracted characters; split the document.")
        if self.source_date > date.today() or self.review_on < self.source_date:
            raise ValueError("Source date cannot be in the future; review date cannot precede it.")
        if self.url and not self.url.startswith(("https://", "http://")):
            raise ValueError("Source links must begin with https:// or http://.")
        if self.kind != "Research" and not self.synthetic:
            raise ValueError("This public prototype accepts fictional customer evidence only.")
        if self.kind == "Research" and not self.synthetic and not self.url:
            raise ValueError("External research requires an original source URL.")
        if self.expected_action:
            if self.expected_action not in ACTIONS or self.kind != "Says" or not self.customer_id:
                raise ValueError("An expectation requires customer-linked Says evidence and a known action.")
            if not self.expected_by or self.expected_by < self.source_date:
                raise ValueError("Expected action deadline must be on or after the statement date.")
            if not self.expectation_quote or not any(self.expectation_quote in t for t in self.chunks.values()):
                raise ValueError("Expectation must cite an exact passage in this source.")
            if not self.expectation_reviewer:
                raise ValueError("A named reviewer must confirm the expected action.")
        return self


class Assessment(Record):
    evidence_kind: Literal["Says", "Does", "Research"] | None = None
    id: str
    source_id: str
    source_revision: int
    hypothesis_id: str
    hypothesis_version: int
    chunk: str
    quote: str = Field(min_length=1)
    stance: Literal["Supports", "Contradicts", "Unclear"]
    rationale: str = Field(min_length=1)
    limitations: str = ""
    status: Literal["Pending", "Approved", "Rejected", "Needs review"] = "Pending"
    origin: str
    created_at: str
    original: dict = Field(default_factory=dict)
    reviews: list[dict] = Field(default_factory=list)


class Change(Record):
    id: str
    version: int
    on: date
    description: str = Field(min_length=1)
    hypotheses: list[str] = Field(min_length=1)
    author: str = Field(min_length=1)


class Decision(Record):
    id: str
    hypothesis_id: str
    hypothesis_version: int
    context_version: int
    action: Literal["Keep testing", "Double down", "Revise", "Retire"]
    rationale: str = Field(min_length=1)
    next_test: str = Field(min_length=1)
    assessment_ids: list[str]
    author: str = Field(min_length=1)
    created_at: str
    evidence_snapshot: list[dict] = Field(default_factory=list)
    recommendation_snapshot: dict = Field(default_factory=dict)


class ActivityEvent(Record):
    customer_id: str
    on: date
    activity: Literal["App opened", "Results opened", "Care plan viewed", "Booking viewed"]


class Project(Record):
    ai_report: dict = Field(default_factory=dict)
    activity_events: list[ActivityEvent] = Field(default_factory=list)
    activity_start: date | None = None
    activity_end: date | None = None
    schema_version: Literal[1] = 1
    name: str = "Alaga Evidence Review"
    context_version: int = Field(default=1, ge=1)
    icp: str = "Health-conscious professionals aged 20–34, urban Philippines within service coverage, with their own health budget. Working ICP from v10, slide 5."
    customers: list[Customer]
    hypotheses: list[Hypothesis]
    sources: list[Source]
    assessments: list[Assessment] = Field(default_factory=list)
    changes: list[Change] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    contradiction_reviews: dict[str, list[dict]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def links(self):
        for key in ("customers", "hypotheses", "sources", "assessments", "changes", "decisions"):
            items = getattr(self, key)
            if len({x.id for x in items}) != len(items):
                raise ValueError(f"Duplicate IDs in {key}.")
        if not self.hypotheses or len({c.number for c in self.customers}) != len(self.customers):
            raise ValueError("Hypotheses are required and customer numbers must be unique.")
        cs, hs, ss = ({x.id: x for x in getattr(self, key)} for key in ("customers", "hypotheses", "sources"))
        if (self.activity_start is None) != (self.activity_end is None):
            raise ValueError("Activity coverage needs both start and end dates.")
        if self.activity_start and not self.activity_start <= self.activity_end <= date.today():
            raise ValueError("Invalid activity coverage dates.")
        for e in self.activity_events:
            if e.customer_id not in cs or not self.activity_start or not self.activity_start <= e.on <= self.activity_end:
                raise ValueError("Activity must reference a customer and fall within coverage.")
            if e.on < cs[e.customer_id].purchased_on:
                raise ValueError("Customer activity cannot precede purchase.")
        for s in self.sources:
            if s.customer_id and s.customer_id not in cs:
                raise ValueError(f"Unknown customer on source {s.id}.")
            if s.context_version > self.context_version:
                raise ValueError("Source context version exceeds the project's current version.")
        for a in self.assessments:
            if a.source_id not in ss or a.hypothesis_id not in hs:
                raise ValueError("Assessment references an unknown source/hypothesis.")
            if a.status=="Approved" and ss[a.source_id].kind=="Research" and a.evidence_kind not in (None,"Research"):
                raise ValueError("External research cannot be approved as direct customer evidence.")
            if a.status == "Approved" and not valid_citation(self, a):
                raise ValueError("Approved assessment has an invalid or outdated source citation.")
            if a.status == "Approved" and a.hypothesis_version != hs[a.hypothesis_id].version:
                raise ValueError("Approved assessment references an outdated hypothesis.")
        for change in self.changes:
            if not set(change.hypotheses) <= hs.keys():
                raise ValueError("Change references an unknown hypothesis.")
        aa = {a.id: a for a in self.assessments}
        for d in self.decisions:
            if d.hypothesis_id not in hs or any(i not in aa or aa[i].hypothesis_id != d.hypothesis_id for i in d.assessment_ids):
                raise ValueError("Decision has invalid evidence references.")
            for snapshot in d.evidence_snapshot:
                saved = Assessment.model_validate(snapshot)
                if saved.id not in d.assessment_ids or saved.hypothesis_id != d.hypothesis_id:
                    raise ValueError("Decision snapshot references an unrelated assessment.")
        return self


def get(items, key):
    return next(x for x in items if x.id == key)


def valid_citation(p, a):
    s = get(p.sources, a.source_id)
    return a.source_revision == s.revision and a.chunk in s.chunks and a.quote in s.chunks[a.chunk]


def assessment_kind(p, a):
    return getattr(a,"evidence_kind",None) or get(p.sources,a.source_id).kind


def current_assessments(p, hid=None, customer_ids=None):
    return [a for a in p.assessments if a.status == "Approved" and (not hid or a.hypothesis_id == hid)
            and not get(p.sources, a.source_id).archived and valid_citation(p, a)
            and a.hypothesis_version == get(p.hypotheses, a.hypothesis_id).version
            and (customer_ids is None or assessment_kind(p,a) == "Research"
                 or get(p.sources,a.source_id).customer_id in customer_ids)]


def freshness(p, s, hid=None, today=None):
    today = today or date.today()
    flags = []
    if s.review_on <= today:
        flags.append("Review due")
    relevant = {hid} if hid else {a.hypothesis_id for a in p.assessments if a.source_id == s.id}
    if any(c.version > s.context_version and c.on <= today and (not relevant or relevant.intersection(c.hypotheses)) for c in p.changes):
        flags.append("Context changed")
    return "; ".join(flags) or "Current"


def edit_source(p, source_id, values):
    old = get(p.sources, source_id)
    candidate = Source.model_validate({**old.model_dump(), **values,
        "revision": old.revision + 1, "history": old.history + [old.model_dump(mode="json", exclude={"history"})]})
    if candidate.customer_id and candidate.customer_id not in {c.id for c in p.customers}:
        raise ValueError("Unknown customer.")
    p.sources[p.sources.index(old)] = candidate
    for a in p.assessments:
        if a.source_id == source_id and a.status != "Rejected":
            a.status = "Needs review"
    return candidate


def add_assessment(p, source_id, hid, chunk, quote, stance, rationale, limitations="", origin="Manual", evidence_kind=None):
    s, h = get(p.sources, source_id), get(p.hypotheses, hid)
    if chunk not in s.chunks or not quote.strip() or quote.strip() not in s.chunks[chunk]:
        raise ValueError("Quotation must match the selected source passage exactly.")
    original = dict(hypothesis_id=hid, chunk=chunk, quote=quote.strip(), stance=stance,
                    rationale=rationale, limitations=limitations, evidence_kind=evidence_kind)
    a = Assessment(id=uid("A"), source_id=s.id, source_revision=s.revision,
        hypothesis_version=h.version, **original, origin=origin, created_at=now(), original=original)
    # Avoid inflating the evidence table when the same analysis is run twice.
    if any(x.source_id == s.id and x.source_revision == s.revision and x.hypothesis_id == hid
           and x.hypothesis_version == h.version and x.quote == a.quote and x.status != "Rejected" for x in p.assessments):
        raise ValueError("This passage already has an assessment for this hypothesis.")
    p.assessments.append(a)
    return a


def review_assessment(p, aid, stance, quote, chunk, rationale, limitations, status, reviewer, evidence_kind=None):
    if not reviewer.strip():
        raise ValueError("Enter a reviewer name.")
    a = get(p.assessments, aid)
    s, h = get(p.sources, a.source_id), get(p.hypotheses, a.hypothesis_id)
    if status == "Approved" and (s.archived or chunk not in s.chunks or not quote.strip() or quote.strip() not in s.chunks[chunk]):
        raise ValueError("Approval requires a current, exact source quotation.")
    kind=evidence_kind or getattr(a,"evidence_kind",None) or s.kind
    if status=="Approved" and s.kind=="Research" and kind!="Research":
        raise ValueError("External research remains Research, including quoted interviews. It is not a direct Alaga customer observation.")
    candidate = Assessment.model_validate({**a.model_dump(), "evidence_kind":kind, "stance": stance, "quote": quote,
        "chunk": chunk, "rationale": rationale, "limitations": limitations, "status": status,
        "source_revision": s.revision, "hypothesis_version": h.version,
        "reviews": a.reviews + [{"at": now(), "reviewer": reviewer, "before": a.model_dump(exclude={"reviews"}),
            "status": status, "stance": stance, "quote": quote, "rationale": rationale, "limitations": limitations, "evidence_kind":kind}]})
    p.assessments[p.assessments.index(a)] = candidate


def revise_hypothesis(p, hid, statement, reviewer):
    h = get(p.hypotheses, hid)
    if not statement.strip() or not reviewer.strip():
        raise ValueError("Statement and reviewer are required.")
    h.history.append({"version": h.version, "statement": h.statement, "at": now(), "reviewer": reviewer})
    h.statement = statement.strip()
    h.version += 1
    for a in p.assessments:
        if a.hypothesis_id == hid and a.status != "Rejected":
            a.status = "Needs review"


def triangulation(p, customer_ids=None):
    rows = []
    for h in p.hypotheses:
        aa = current_assessments(p, h.id, customer_ids)
        row = {"ID": h.id, "Hypothesis": h.title}
        for kind in KINDS:
            for stance in STANCES:
                row[f"{kind}: {stance}"] = len({a.source_id for a in aa if a.stance == stance and assessment_kind(p,a) == kind})
        linked = {a.source_id for a in aa}
        row["Review flags"] = sum(freshness(p, get(p.sources, sid), h.id) != "Current" for sid in linked)
        row["Hypothesis review due"] = h.review_on <= date.today()
        row["Context changed"] = any(c.on <= date.today() and h.id in c.hypotheses and c.version > max(
            [d.context_version for d in p.decisions if d.hypothesis_id == h.id and d.hypothesis_version == h.version] or [1]) for c in p.changes)
        decisions = [d for d in p.decisions if d.hypothesis_id == h.id]
        row["Last human decision"] = decisions[-1].action if decisions else "Not decided"
        if decisions and (decisions[-1].hypothesis_version != h.version or row["Context changed"]):
            row["Last human decision"] += " (earlier context)"
        rows.append(row)
    return pd.DataFrame(rows)


def hypothesis_thesis(p, hid, customer_ids=None):
    """Conservative review heuristic, not a model inference or statistical finding.

    Count customers once. Research is context, not customer validation. A strong
    directional draft requires both Says and Does across acquisition cohorts.
    """
    aa = current_assessments(p, hid, customer_ids)
    fresh = [a for a in aa if freshness(p, get(p.sources, a.source_id), hid) == "Current"]
    stale_ids = sorted({a.source_id for a in aa if a not in fresh})
    positions = {stance: {kind: set() for kind in ("Says", "Does")} for stance in ("Supports", "Contradicts")}
    for a in fresh:
        s = get(p.sources, a.source_id)
        if s.customer_id and assessment_kind(p,a) in ("Says", "Does") and a.stance in positions:
            positions[a.stance][assessment_kind(p,a)].add(s.customer_id)
    support = positions["Supports"]["Says"] | positions["Supports"]["Does"]
    against = positions["Contradicts"]["Says"] | positions["Contradicts"]["Does"]
    mixed = support & against
    # A customer with mixed findings is not counted as a clear directional vote.
    support -= mixed
    against -= mixed

    def cohorts(ids):
        return {1 if get(p.customers, i).number <= 10 else 2 if get(p.customers, i).number <= 30
                else 3 if get(p.customers, i).number <= 100 else 4 for i in ids}

    def corroborated(stance, ids):
        return len(positions[stance]["Says"] & positions[stance]["Does"] & ids)

    ns, nc = len(support), len(against)
    cs, cc = corroborated("Supports", support), corroborated("Contradicts", against)
    unresolved = [r for r in contradictions(p) if hid in r["hypothesis"].split(", ")
                  and r["status"] != "Explained / dismissed"
                  and (customer_ids is None or r["customer"] in customer_ids)]
    h = get(p.hypotheses, hid)
    status, recommendation, action = "Limited evidence", "Keep testing", "Keep testing"
    thesis = "There is not enough current, corroborated customer evidence to judge this hypothesis."
    next_test = "Collect an interview and a relevant action record for the same customers in the next cohort."
    if ns >= 5 and len(cohorts(support)) >= 2 and cs >= 2 and ns >= 2 * max(nc, 1) and not mixed and not unresolved:
        status, recommendation, action = "Well evidenced in this sample", "Consider doubling down", "Double down"
        thesis = "Customer accounts and behavior consistently support this hypothesis across cohorts. Test whether the pattern repeats before expanding recruitment."
        next_test = "Repeat the offer in a new cohort and check whether customer value and appropriate follow-through persist."
    elif nc >= 5 and len(cohorts(against)) >= 2 and cc >= 2 and nc >= 2 * max(ns, 1) and not mixed and not unresolved:
        status, recommendation, action = "Consistently challenged", "Consider retiring", "Retire"
        thesis = "Current customer accounts and behavior repeatedly challenge this wording across cohorts. Consider retiring or replacing it after reviewing plausible alternative explanations."
        next_test = "Review the counterevidence and test the strongest alternative explanation before retiring the hypothesis."
    elif mixed or (ns >= 2 and nc >= 2):
        status, recommendation, action = "Mixed evidence", "Consider a pivot", "Revise"
        thesis = "Customer evidence points in both directions. The problem may depend on segment, trigger, or delivery conditions."
        next_test = "Compare the supporting and contradicting customers; test a narrower statement in the next cohort."
    elif ns >= 2 and cs >= 1:
        status = "Emerging support"
        thesis = "There is early support from both customer accounts and behavior, but it has not met the cross-cohort review threshold."
    elif nc >= 2 and cc >= 1:
        status = "Emerging counterevidence"
        thesis = "Some customer accounts and behavior challenge the hypothesis. Gather a repeat observation before recommending retirement."
    if unresolved:
        status, recommendation, action = "Unresolved contradictions", "Investigate the mismatch", "Keep testing"
        thesis = "Linked statements and actions disagree. Resolve the mismatch before treating this hypothesis as supported or disproved."
        next_test = "Review each linked mismatch with the customer and check timing, access, affordability, and relevance of the action."
    # Never issue an escalation/retirement draft while linked evidence needs refresh.
    if stale_ids or h.review_on <= date.today():
        status, recommendation, action = "Needs revalidation", "Revalidate first", "Keep testing"
        thesis = "The evidence base needs a freshness review before making a strategic call. Earlier findings remain available, but they should not drive a new decision without revalidation."
        next_test = "Review the flagged sources against the current offer and ICP, then reapprove relevant links."
    return {"hypothesis_id": hid, "hypothesis_version": h.version, "context_version": p.context_version,
            "status": status, "recommendation": recommendation, "action": action, "thesis": thesis,
            "next_test": next_test, "supporting_customers": ns, "contradicting_customers": nc,
            "mixed_customers": len(mixed), "supporting_cohorts": len(cohorts(support)),
            "contradicting_cohorts": len(cohorts(against)), "corroborated_support": cs,
            "corroborated_contradiction": cc, "stale_sources": stale_ids,
            "unresolved_mismatches": len(unresolved), "assessment_ids": [a.id for a in aa],
            "fresh_assessment_ids": [a.id for a in fresh], "method": "Review rules v1",
            "customer_scope": "All customers" if customer_ids is None else sorted(customer_ids)}


def contradictions(p, today=None):
    """Deterministic candidates, never automatic judgements of truth."""
    today = today or date.today()
    rows = []
    for s in p.sources:
        if s.archived or not s.expected_action or not s.expected_by or s.expected_by > today:
            continue
        c = get(p.customers, s.customer_id)
        e = c.events[s.expected_action]
        if c.observed_through < s.expected_by or e.status in ("Unknown", "Not applicable"):
            continue
        if e.status == "Completed" and e.on <= s.expected_by:
            continue
        behavior = next((x for x in p.sources if x.id == "B-" + c.id), None)
        if not behavior or behavior.archived:
            continue
        key = f"expect:{s.id}:r{s.revision}:{behavior.id}:r{behavior.revision}"
        rows.append({"id": key, "type": "Intention / action", "customer": c.id,
            "hypothesis": ", ".join(sorted({a.hypothesis_id for a in current_assessments(p) if a.source_id == s.id})) or "Unlinked",
            "sources": [s.id, behavior.id], "detail": f"Expected {s.expected_action} by {s.expected_by}; {e.status.lower()}" + (f" on {e.on}" if e.on else "") + f". Observed through {c.observed_through}.",
            "freshness": freshness(p, s) + " / " + freshness(p, behavior)})
    aa = current_assessments(p)
    seen = set()
    for a, b in combinations(aa, 2):
        if a.hypothesis_id != b.hypothesis_id or {a.stance, b.stance} != {"Supports", "Contradicts"}:
            continue
        sa, sb = get(p.sources, a.source_id), get(p.sources, b.source_id)
        if not sa.customer_id or sa.customer_id != sb.customer_id or {assessment_kind(p,a), assessment_kind(p,b)} != {"Says", "Does"}:
            continue
        if abs((sa.source_date - sb.source_date).days) > 90 or sa.context_version != sb.context_version:
            continue
        key = f"opposing:{a.hypothesis_id}:" + ":".join(sorted([f"{sa.id}-r{sa.revision}", f"{sb.id}-r{sb.revision}"]))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"id": key, "type": "Opposing reviewed evidence", "customer": sa.customer_id,
            "hypothesis": a.hypothesis_id, "sources": [sa.id, sb.id],
            "detail": "Reviewed Says and Does evidence take opposing positions within 90 days and the same context version.",
            "freshness": freshness(p, sa, a.hypothesis_id) + " / " + freshness(p, sb, a.hypothesis_id)})
    for row in rows:
        history = p.contradiction_reviews.get(row["id"], [])
        row["status"] = history[-1]["status"] if history else "Open"
    return rows


def behavior_source(c, context_version):
    text = "\n".join(f"{action}: {event.status}" + (f" on {event.on}" if event.on else "") for action, event in c.events.items())
    text += f"\nObserved through {c.observed_through}. Satisfaction: {c.satisfaction}/5."
    return Source(id="B-" + c.id, title=f"{c.id} action record", kind="Does", customer_id=c.id,
        chunks={"Customer action record": text}, source_date=c.observed_through,
        review_on=c.observed_through + timedelta(days=90), context="Synthetic customer observations; no causal interpretation.",
        context_version=context_version)


def save_customers(p, customers, replace_existing=False):
    ids = {c.id for c in p.customers}
    if not replace_existing and ids & {c.id for c in customers}:
        raise ValueError("Customer IDs already exist. Choose update matching IDs explicitly.")
    combined = {c.id: c for c in p.customers}
    combined.update({c.id: c for c in customers})
    if len({c.number for c in combined.values()}) != len(combined):
        raise ValueError("Acquisition numbers must be unique, including existing customers.")
    for c in customers:
        s = behavior_source(c, p.context_version)
        old = next((x for x in p.sources if x.id == s.id), None)
        if old:
            edit_source(p, old.id, s.model_dump(exclude={"id", "revision", "history"}))
        else:
            p.sources.append(s)
    p.customers = list(combined.values())


def customer_frame(customers):
    rows = []
    for c in customers:
        r = c.model_dump(mode="json", exclude={"events"})
        for action, event in c.events.items():
            r[action] = event.status
            r[action + "_date"] = event.on.isoformat() if event.on else ""
        rows.append(r)
    return pd.DataFrame(rows)


def parse_customers(frame):
    if frame.empty or len(frame) > 1000:
        raise ValueError("Import between 1 and 1,000 fictional customers.")
    rows = []
    for i, raw in enumerate(frame.fillna("").to_dict("records"), start=2):
        try:
            events = {a: {"status": raw.pop(a), "on": raw.pop(a + "_date") or None} for a in ACTIONS}
            rows.append(Customer.model_validate({**raw, "events": events}))
        except (KeyError, ValueError) as exc:
            raise ValueError(f"CSV row {i}: use the downloadable template. {exc}") from exc
    if len({c.id for c in rows}) != len(rows) or len({c.number for c in rows}) != len(rows):
        raise ValueError("Duplicate customer IDs or acquisition numbers within CSV.")
    return rows


def load_demo():
    return Project.model_validate_json((ROOT / "data" / "demo_project.json").read_text(encoding="utf-8"))


def import_project(data):
    if len(data) > 10_000_000:
        raise ValueError("Project file exceeds 10 MB.")
    p = Project.model_validate_json(data)
    # Imported snapshots retain their evidence and decisions; no code is executed.
    return p
