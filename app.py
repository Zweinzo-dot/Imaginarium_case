"""Alaga Evidence Review: a session-local Streamlit prototype."""
from datetime import date, timedelta
from io import BytesIO
import os
from analytics import cohort, activity_report
import pandas as pd
import streamlit as st
from evidence import (ACTIONS, EVENT_STATES, KINDS, STANCES, Change, Customer, Decision,
    Event, Source, add_assessment, contradictions, current_assessments, customer_frame,
    edit_source, freshness, get, import_project, load_demo, now, parse_customers,
    review_assessment, revise_hypothesis, save_customers, triangulation, uid)
from evidence import hypothesis_thesis, assessment_kind, Project
from ai_workspace import analyze_workspace, fingerprint
from local_ai import DemoClient, OllamaClient, ollama_models, scenarios
from analysis_tools import accept_proposals, ai_proposals, extract_document


def table(rows):
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def done(message):
    st.session_state.notice = message
    st.rerun()


def secret(name, default=""):
    try:
        return str(st.secrets.get(name, os.getenv(name, default)))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return os.getenv(name, default)


def analysis_mode():
    return st.session_state.get("analysis_mode", "OpenAI" if st.session_state.get("ai_session_key") or secret("ENABLE_LIVE_AI","false").lower()=="true" else "Demo scenarios")


def analysis_client():
    return DemoClient() if analysis_mode()=="Demo scenarios" else OllamaClient() if analysis_mode()=="Local Ollama" else None


def mode_picker():
    modes=["Demo scenarios","Local Ollama","OpenAI"]
    st.radio("Analysis mode",modes,key="analysis_mode",horizontal=True)


def ai_config():
    """Credentials are session-local or server-managed; never part of Project."""
    mode=analysis_mode()
    if mode=="Demo scenarios": return True,"demo","Prepared scenarios v1"
    if mode=="Local Ollama": return True,"local",st.session_state.get("ollama_model","qwen3:0.6b")
    key=st.session_state.get("ai_session_key", "")
    if key:
        return True, key, st.session_state.get("ai_session_model", "gpt-4o-mini")
    enabled=secret("ENABLE_LIVE_AI","false").lower()=="true"
    return enabled, secret("OPENAI_API_KEY"), secret("OPENAI_MODEL","gpt-4o-mini")


def connect_ai():
    key=st.session_state.get("ai_key_input", "").strip()
    model=st.session_state.get("ai_model_input", "").strip()
    if not key or not model:
        st.session_state.ai_setup_error="Enter an API key and model ID."
        return
    st.session_state.ai_session_key=key
    st.session_state.ai_session_model=model
    st.session_state.ai_key_input=""
    st.session_state.pop("ai_setup_error",None)
    st.session_state.pop("ai_connection_result",None)
    st.session_state.notice="API credentials saved for this session. Test the connection, then analyze a source in Evidence."


def disconnect_ai():
    for name in ("ai_session_key","ai_session_model","ai_key_input","ai_connection_result"):
        st.session_state.pop(name,None)


def navigate(page):
    st.session_state.workspace=page


def ai_setup_page(p):
    st.header("AI setup")
    mode_picker()
    if analysis_mode()!="OpenAI":
        if analysis_mode()=="Demo scenarios":
            st.info("Simulated AI: prepared responses matched to exact demo passages. No model, account or network request.")
        else:
            st.text_input("Local model",value=st.session_state.get("ollama_model","qwen3:0.6b"),key="ollama_model")
            st.caption("Streamlit calls http://127.0.0.1:11434 on this computer. No cloud fallback. A hosted Streamlit app cannot reach your PC's localhost.")
            if st.button("Check Ollama"):
                try:
                    installed=ollama_models()
                    if st.session_state.ollama_model in installed: st.success("Selected model is installed: "+st.session_state.ollama_model)
                    else: st.warning("Model not installed. Installed models: "+", ".join(installed))
                except Exception:st.error("Ollama is not reachable. Start Ollama on this PC.")
        st.button("Go to AI analysis",on_click=navigate,args=("AI analysis",))
        return
    enabled,key,model=ai_config()
    st.write("Connect OpenAI to analyze the customer base, link evidence and draft conclusions. Final decisions remain manual.")
    st.link_button("Create an OpenAI API key","https://platform.openai.com/api-keys")
    st.caption("API usage is billed to the key's account. Use a model your project can access.")
    with st.form("ai_connection"):
        st.text_input("OpenAI API key",type="password",key="ai_key_input")
        st.text_input("Model ID",value=model,key="ai_model_input")
        st.caption("Stored in this server session only, never in project exports or files. On a hosted app, the app server receives your key. Use only a deployment you trust.")
        st.form_submit_button("Use key for this session",on_click=connect_ai)
    if st.session_state.get("ai_setup_error"):
        st.error(st.session_state.ai_setup_error)
    if enabled and key:
        st.info(f"Configured: {model} · {'session key' if st.session_state.get('ai_session_key') else 'server key'}. Connection is verified only when tested.")
        if st.button("Test API connection"):
            try:
                from openai import OpenAI
                with st.spinner("Checking model access…"):
                    with OpenAI(api_key=key,timeout=15,max_retries=0) as client:
                        client.models.retrieve(model)
                st.session_state.ai_connection_result=(True,"API connection verified; model is accessible. This check sends no evidence and does not test generation or billing quota.")
            except Exception:
                st.session_state.ai_connection_result=(False,"Connection failed. Check the API key, model ID, project permissions and network connection. Your evidence was not sent.")
        result=st.session_state.get("ai_connection_result")
        if result:
            (st.success if result[0] else st.error)(result[1])
        if st.session_state.get("ai_session_key"):
            st.button("Remove session key",on_click=disconnect_ai)
    else:
        st.caption("No active connection.")
    st.button("Go to Evidence",on_click=navigate,args=("Evidence",),type="primary")
    st.write("Open AI analysis to analyze the whole workspace and enable automatic updates after saved uploads or edits. Evidence also offers analysis of individual passages.")
    st.button("Go to AI analysis",on_click=navigate,args=("AI analysis",))
    with st.expander("Configure a deployment"):
        st.write("For a persistent local setup, add the values below to `.streamlit/secrets.toml`. On Community Cloud, use the app's Secrets settings. Never commit a key to GitHub.")
        st.code('ENABLE_LIVE_AI = "true"\nOPENAI_API_KEY = "your-key"\nOPENAI_MODEL = "gpt-4o-mini"',language="toml")
        st.link_button("OpenAI setup guide","https://developers.openai.com/api/docs/quickstart")



def open_ai_citation(aid):
    a=get(st.session_state.project.assessments,aid)
    st.session_state[f"review_link_{a.source_id}"]=aid
    st.session_state.evidence_search=""
    open_review_source(a.source_id)


def run_workspace_ai(p):
    enabled,key,model=ai_config()
    if not enabled or not key:
        st.warning("Connect a model in AI setup first.")
        return p
    st.session_state.ai_last_attempt=fingerprint(p)+analysis_mode()+model
    try:
        with st.status("Analyzing workspace…",expanded=True) as status:
            client=analysis_client()
            if isinstance(client,OllamaClient): client.progress=lambda message: status.update(label=message)
            updated=analyze_workspace(p,key,model,client=client,provider=analysis_mode(),
                source_ids=st.session_state.get("local_source_ids",[]) if analysis_mode()=="Local Ollama" and not st.session_state.get("local_all_sources") else None,
                progress=lambda message: status.update(label=message))
            status.update(label="Analysis ready. Links are drafts; decisions remain yours.",state="complete")
        st.session_state.project=updated
        st.session_state.pop("ai_batch_error",None)
        return updated
    except Exception as exc:
        message=str(exc) if isinstance(exc,(ValueError,TypeError,AttributeError)) else "AI request failed. Check model access, quota and connection."
        st.session_state.ai_batch_error=message
        st.error(message+" Your saved data and previous analysis are unchanged. Retry from AI analysis.")
        return p


def workspace_findings(p,area,full=False):
    report=getattr(p,"ai_report",{}) or {}
    if not report:
        if area=="Dashboard":
            st.info("Open AI analysis to try prepared demo scenarios without an account, or connect a local model.")
        return
    stale=report.get("input_hash")!=fingerprint(p) or report.get("provider","OpenAI")!=analysis_mode()
    with st.container(border=True):
        st.subheader("Preliminary findings" if full else "AI summary")
        st.caption(f"{'Out of date — rerun AI analysis' if stale else 'Current inputs'} · {report.get('model','')} · {report.get('generated_at','')} · whole project, independent of page filters")
        st.caption("SIMULATED — prepared responses and calculated counts, not live AI." if report.get("provider")=="Demo scenarios" else "AI draft interpretations may use unreviewed links. Final decisions are manual.")
        selected_area=st.selectbox("Summary section",["Dashboard","Hypotheses","Customers","Evidence","Contradictions","Decisions"]) if full else area
        findings=[f for f in report.get("findings",[]) if f["area"]==selected_area]
        if not findings:
            st.info("No findings for this section yet. Run Analyze workspace to generate them.")
        if len(findings)>1:
            targets=[f["target"] for f in findings]
            selected=st.selectbox("Summary hypothesis" if selected_area=="Hypotheses" else "Summary segment",targets,
                format_func=lambda target:next((f"{h.id} - {h.title}" for h in p.hypotheses if h.id==target),target),key=f"summary_target_{area}_{selected_area}")
            findings=[f for f in findings if f["target"]==selected]
        for i,f in enumerate(findings):
            title=next((f"{h.id} - {h.title}" for h in p.hypotheses if h.id==f["target"]),f["target"])
            if title!="All": st.markdown(f"**{title}**")
            st.write(f["conclusion"])
            with st.expander(f"Evidence & next test ({len(f['assessment_ids'])} cited links)",expanded=False):
                st.write("Next test: "+f["next_test"])
                st.caption("Limits: "+f["limitations"])
                for aid in f["assessment_ids"]:
                    a=next((a for a in p.assessments if a.id==aid),None)
                    if not a:
                        st.caption(f"{aid}: no longer available")
                        continue
                    source=get(p.sources,a.source_id)
                    st.write(f"{a.id} · {a.hypothesis_id} · {a.stance} · {a.status} · {freshness(p,source,a.hypothesis_id)}")
                    saved=report.get("citations",{}).get(aid,{})
                    st.write(saved.get("quote",a.quote))
                    st.caption(f"At analysis: {saved.get('status',a.status)} · source revision {saved.get('source_revision',a.source_revision)}")
                    st.button("Open source / review",key=f"finding_{area}_{i}_{aid}",on_click=open_ai_citation,args=(aid,))


def demo_scenario_result(p):
    result=p.ai_report.get('scenario_run')
    if not result:return
    with st.container(border=True):
        st.subheader('What changed in this demo')
        st.markdown(f"**{result['title']}** · {result['hypothesis_id']} · {result['customer_id']}")
        st.caption('Prepared scenario interpretation. This is the latest scenario run; earlier scenario evidence remains in the workspace.')
        st.markdown(f"**Finding:** {result['finding']}")
        st.markdown(f"**Suggested response:** {result['implication']}")
        st.markdown(f"**Next test:** {result['test']}")
        table([{'At scenario run':'Pending links for this hypothesis','Before':str(result['before_pending']),'After':str(result['after_pending'])},
               {'At scenario run':'Reviewed recommendation','Before':result['before_recommendation'],'After':result['after_recommendation']}])
        if result['new_links']==0:
            st.info('This scenario was already applied to this customer. Its existing classification was reused; no duplicate evidence was added.')
        else:
            st.success('Added one interview passage and one draft classification. Customer action metrics were not changed.')
        st.caption('The interpretation changes immediately. Reviewed recommendations depend on approved evidence, so one pending interview does not flip the strategic recommendation. The table is a snapshot at the time of this run.')
        a=next((a for a in p.assessments if a.id==result['assessment_id']),None)
        if a:
            st.write(f"Current classification: **{a.stance} · {a.status}** ({a.id})")
            st.button('Review this scenario evidence',on_click=open_ai_citation,args=(a.id,))
        with st.expander('Exact passage added'):
            st.write(result['quote'])
            st.caption(f"Source: {result['source_id']} · run at {result['at']}")


def ai_analysis_page(p):
    st.header("AI analysis")
    st.write("Analyze interviews, customer actions and research together. AI links evidence to hypotheses and drafts segment conclusions; you decide what to do.")
    if analysis_mode()=='Demo scenarios':demo_scenario_result(p)
    with st.expander('Overall workspace findings',expanded=not bool(p.ai_report.get('scenario_run'))):
        workspace_findings(p,"AI analysis",full=True)
    st.subheader("Run or update analysis")
    mode_picker()
    mode=analysis_mode()
    enabled,key,model=ai_config()
    st.button("AI connection settings",on_click=navigate,args=("AI setup",))
    consent=True
    if mode=="OpenAI":
        consent=st.checkbox("Send workspace data to OpenAI for analysis",key="workspace_ai_consent",
            help="Includes all active source text, customer attributes and notes, hypotheses and evidence reviews.")
    elif mode=="Demo scenarios":
        st.info("Simulated AI: exact scenario passages return prepared classifications. Other text is left unclassified. No API account needed.")
        st.subheader('Try a scenario')
        from local_ai import run_demo_scenario, SCENARIO_STORIES
        scenario=st.selectbox("Prepared scenario",scenarios(),format_func=lambda x:x["title"])
        st.write(SCENARIO_STORIES[scenario['id']]['finding'])
        customer=st.selectbox('Scenario customer',[c.id for c in p.customers])
        st.caption('Run adds the prepared interview, classifies it, and shows the change above. It never approves evidence or saves a decision. Repeating the same scenario/customer does not add duplicates.')
        if st.button('Run selected demo scenario',type='primary',disabled=not p.customers):
            try:
                st.session_state.project=run_demo_scenario(p,scenario['id'],customer)
                st.rerun()
            except ValueError as exc:st.error(str(exc))
        with st.expander("Or download and upload the scenario yourself"):
            st.write(scenario["text"])
            st.download_button("Download interview TXT",scenario["text"],scenario["id"]+".txt","text/plain")
            sample=customer_frame(p.customers[:1]).copy()
            if not sample.empty:
                if "note" in sample.columns:sample["note"]=scenario["text"]
                st.download_button("Download customer update CSV",sample.to_csv(index=False),scenario["id"]+".csv","text/csv")
            st.caption("Upload the TXT in Evidence and save it, or apply the CSV in Customers with Update matching IDs. Then Analyze workspace. You can also paste this exact paragraph into an interview or customer note. Use each scenario with its original hypothesis wording.")
    else:
        st.caption("Real local inference via Ollama. Selected sources get new links; conclusions summarize existing workspace links using a balanced sample. No cloud calls.")
        if model=="qwen3:0.6b": st.warning("Starter model: fast after warm-up, but it can misclassify even clear statements. Review every proposed link; use Demo scenarios for a predictable presentation.")
        ids=[s.id for s in p.sources if not s.archived]
        st.checkbox("Analyze all sources and customer notes",key="local_all_sources",help="Longer run: includes the whole customer base and all active sources. Otherwise only the selected sources receive new classifications.")
        st.multiselect("Sources to analyze locally",ids,default=["I-013"] if "I-013" in ids else [s.id for s in p.sources if s.kind=="Says"][-1:],key="local_source_ids",format_func=lambda sid:f"{sid} · {get(p.sources,sid).title}")
        st.caption("Start with 1–3 sources; local inference can take several minutes. Select additional sources when ready.")
    st.checkbox("Automatically update after saved data changes",key="workspace_ai_auto",disabled=not consent or mode=="Local Ollama",
        help="After your first run, saved uploads, edits and reviews trigger analysis while this session is open. New and changed sources are analyzed, then conclusions are refreshed. API charges apply; navigation alone does not rerun analysis.")
    if st.button("Analyze workspace",type="primary",disabled=not(enabled and key and consent) or (mode=="Local Ollama" and not st.session_state.get("local_source_ids") and not st.session_state.get("local_all_sources"))):
        run_workspace_ai(p)
        st.rerun()
    if not(enabled and key):
        st.caption("Connect your API key in AI setup to enable analysis.")
    if st.session_state.get("ai_batch_error"):
        st.warning(st.session_state.ai_batch_error+" Automatic retry is paused for these inputs. Use Analyze workspace to retry.")
    report=getattr(p,"ai_report",{}) or {}
    if report:
        st.caption(f"Last run: {report.get('sources_analyzed',0)} sources in analysis scope · {report.get('new_links',0)} new draft links · {report.get('provider','OpenAI')}")
        if report.get("provider")=="Local Ollama": st.caption("Local mode classifies the chosen source scope. Conclusions use sampled excerpts from existing workspace links.")
        with st.expander("Segment metrics used by AI"):
            table(report.get("metrics",[]))
            st.caption("Default power-user weights, cutoff 7, actions within 30 days. These metrics are separate from exploratory scoring controls in Customers.")
    pending=[a for a in p.assessments if a.status in ("Pending","Needs review") and not get(p.sources,a.source_id).archived]
    with st.expander(f"Review proposed links ({len(pending)})"):
        if pending:
            table(assessment_rows(p,pending))
            aid=st.selectbox("Proposed link to review",[a.id for a in pending],format_func=lambda aid:f"{aid} · {get(p.assessments,aid).source_id} · {get(p.assessments,aid).hypothesis_id}")
            st.button("Review selected proposal",on_click=open_ai_citation,args=(aid,))
        else:
            st.caption("No links waiting for review.")


def review_history_rows(p, source_id=None):
    rows=[]
    for a in p.assessments:
        if source_id and a.source_id!=source_id:
            continue
        for n,r in enumerate(a.reviews,1):
            rows.append({"Reviewed at (UTC)":r["at"],"Reviewer":r["reviewer"],"Source":a.source_id,
                         "Link":a.id,"Hypothesis":a.hypothesis_id,"Review #":n,
                         "Outcome":r["status"],"Position":r["stance"],"Rationale":r["rationale"],"Quotation":r["quote"]})
    return sorted(rows,key=lambda row:(row["Reviewed at (UTC)"],row["Review #"]),reverse=True)


def concise(text):
    """Remove known demo boilerplate from display copy, never from source quotations."""
    replacements = {
        "Fictional interview ": "Interview ",
        "Fictional buyer interview. ": "Buyer interview. ",
        "No real person was interviewed.": "",
        "One synthetic interview. ": "One interview. ",
        "Synthetic customer observations; no causal interpretation.": "Action record; no causal interpretation.",
        "Fictional customer generated for the Alaga learning demo.": "",
        "The fictional customer": "The customer",
        "this fictional action record": "this action record",
        " (fictional)": "",
    }
    for old,new in replacements.items():
        text=text.replace(old,new)
    return text.strip()


def open_recommendation(hid, recommendation):
    st.session_state.workspace = "Decisions"
    st.session_state.decision_hypothesis = hid
    st.session_state.decision_draft = recommendation


def customer_scope(p, prefix):
    """Shared business filters; empty selections mean all."""
    a,b,c=st.columns(3)
    segments=a.multiselect("Segments",sorted({x.segment for x in p.customers}),key=prefix+"_segments")
    channels=b.multiselect("Channels",sorted({x.channel for x in p.customers}),key=prefix+"_channels")
    cohorts=c.multiselect("Cohorts",[v for v in ["1–10","11–30","31–100","101+"] if any(cohort(x.number)==v for x in p.customers)],key=prefix+"_cohorts")
    return {x.id for x in p.customers if (not segments or x.segment in segments)
            and (not channels or x.channel in channels) and (not cohorts or cohort(x.number) in cohorts)},bool(segments or channels or cohorts)


def dashboard_page(p):
    st.header("Dashboard")
    workspace_findings(p,"Dashboard")
    if not getattr(p,"activity_start",None):
        st.info("This project has no app-activity records yet.")
        st.caption("Load the bundled usage events for matching demo customers. Interviews, reviews and decisions are preserved.")
        if st.button("Load demo activity"):
            demo=load_demo()
            known={c.id:c for c in p.customers}
            values=p.model_dump()
            values.update(activity_start=demo.activity_start,activity_end=demo.activity_end,
                activity_events=[e.model_dump() for e in demo.activity_events if e.customer_id in known and e.on>=known[e.customer_id].purchased_on])
            from evidence import Project
            st.session_state.project=Project.model_validate(values)
            done("Demo activity loaded. Existing evidence and decisions preserved.")
        return
    st.caption(f"Activity recorded {p.activity_start} to {p.activity_end} · business usage, not server uptime")
    with st.expander("Dashboard filters"):
        ids,_=customer_scope(p,"dashboard")
        as_of=st.date_input("As of",p.activity_end,min_value=p.activity_start,max_value=p.activity_end)
        days=st.selectbox("Timeline",[30,60,90,180],index=2,format_func=lambda n:f"Last {n} days")
    report=activity_report(p,as_of,ids)
    def percent(value):
        return "—" if value is None else f"{value:.1%}"
    a,b,c,d=st.columns(4)
    a.metric("Daily active users",report["dau"],None if report["previous_dau"] is None else f"{report['dau']-report['previous_dau']:+d} vs previous day")
    b.metric("30-day active users",report["mau"] if report["mau"] is not None else "—",None if report["growth"] is None else f"{report['growth']:+.1%} vs prior 30 days")
    c.metric("Inactivity churn",percent(report["churn"]))
    d.metric("Active retention",percent(report["retention"]))
    st.caption(f"As of {as_of} · {report['customers']} paid customers in scope · churn/retention denominator: {report['eligible'] if report['eligible'] is not None else 'incomplete coverage'} previously active customers")
    daily=report["daily"]
    window=daily[daily.Date>=pd.Timestamp(as_of-timedelta(days=days-1))]
    daily_tab,monthly_tab=st.tabs(["Daily activity","Monthly activity"])
    with daily_tab:
        st.line_chart(window.set_index("Date")[["Daily active users","30-day active users"]],height=300,color=["#3478BD","#9CCFF2"],y_label="Customers")
        st.caption("Unique customers per day and rolling 30-day window. Repeat events count once per customer.")
    with monthly_tab:
        months=report["monthly"]
        st.bar_chart(months.set_index("Month")[["Active users"]],height=300,color="#3478BD",y_label="Customers")
        table(months)
        st.caption("Calendar-month unique users. Partial months are marked and are not compared to full months for growth.")
    st.subheader("What changed")
    if report["eligible"] is None:
        st.info("60 recorded days are needed to compare two complete 30-day windows.")
    else:
        st.write(f"**{len(report['retained'])}** stayed active · **{len(report['lost'])}** became inactive · **{len(report['newly_active'])}** became active or returned.")
    a,b=st.columns(2)
    a.metric("New paid customers in last 30 days",int(window.tail(30)["New paid customers"].sum()))
    b.metric("Events on selected day",len(report["events_today"]))
    with st.expander("Daily detail"):
        if report["events_today"]:
            table(report["events_today"])
        else:
            st.caption("No activity recorded on this day within the selected scope.")
        table(window)
        st.download_button("Download activity summary",window.to_csv(index=False),"activity_summary.csv","text/csv")
    with st.expander("Metric definitions"):
        st.write("Active = at least one app-open, results-open, care-plan-view or booking-view event. MAU uses the 30 days ending on the selected date; growth compares that with the preceding non-overlapping 30 days. Inactivity churn = customers active in the preceding window but absent in the current window ÷ preceding-window active customers. Retention uses the same denominator. This is usage churn, not cancellation or revenue churn. New/returned activity does not necessarily mean a new purchase. Undefined ratios and incomplete windows show a dash.")
        st.write("The bundled event log is a fixed demo snapshot. Changing the date filters it; the app does not collect real visitor analytics. Activity is separate from clinical action records and does not alter hypothesis scores.")
    st.button("Explore hypotheses",on_click=navigate,args=("Hypotheses",))


def source_view(p, s, key):
    st.write(f"**{concise(s.title)}**")
    st.caption(f"{s.id} · {s.source_date} · {freshness(p,s)} · {len(s.chunks)} passages")
    if s.customer_id:
        customer=get(p.customers,s.customer_id)
        st.caption(f"{customer.id} · age {customer.age} · {customer.segment}")
    if s.url:
        st.link_button("Open original research", s.url)
    location = st.selectbox("Source passage", list(s.chunks), key=f"passage_{key}_{s.revision}")
    st.text(s.chunks[location])
    if len(s.chunks)>1:
        with st.expander(f"Read all {len(s.chunks)} passages"):
            for label,text in s.chunks.items():
                st.write(f"**{label}**")
                st.write(text)
    with st.expander("Context & history"):
        if getattr(s,"category","Other") != "Other":
            st.write(f"Category: {s.category}")
        if s.context:
            st.write(concise(s.context))
        st.caption(f"Revision {s.revision} · review by {s.review_on}")
        if s.history:
            st.json(s.history, expanded=False)
    if s.expected_action:
        st.caption(f"Expected: {s.expected_action.replace('_',' ')} by {s.expected_by} · {concise(s.expectation_reviewer)}")


def assessment_rows(p, assessments):
    return [{"ID": a.id, "Source": a.source_id, "Type": assessment_kind(p,a),
             "Hypothesis": a.hypothesis_id, "Position": a.stance, "Review": a.status,
             "Freshness": freshness(p,get(p.sources,a.source_id),a.hypothesis_id),
             "Passage": a.chunk, "Quotation": a.quote, "Rationale": concise(a.rationale)} for a in assessments]


def hypotheses_page(p):
    st.header("Hypotheses")
    workspace_findings(p,"Hypotheses")
    st.caption("Test your customer assumptions against approved evidence. Choose a hypothesis, examine both sides, then review the suggested next step.")
    with st.expander("Working ICP"):
        st.write(p.icp)
    scope=st.selectbox("Customer group",["All customers","Ages 20–34","Ages 35+"])
    customer_ids=None if scope=="All customers" else {c.id for c in p.customers if (20<=c.age<=34 if scope=="Ages 20–34" else c.age>=35)}
    if customer_ids is not None:
        st.caption("Age filter only. Research remains visible.")
    with st.expander("Hypothesis filters"):
        scoped,active_filters=customer_scope(p,"hypothesis")
        search=st.text_input("Find hypothesis",placeholder="Title, ID or statement")
        suggested=st.multiselect("Recommendations",["Consider doubling down","Consider a pivot","Consider retiring","Keep testing","Revalidate first","Investigate the mismatch"])
        decisions=st.multiselect("Human decisions",["Not decided","Keep testing","Double down","Revise","Retire"])
    if active_filters:
        customer_ids=scoped if customer_ids is None else customer_ids & scoped
    summary = triangulation(p,customer_ids)
    recommendations={h.id:hypothesis_thesis(p,h.id,customer_ids) for h in p.hypotheses}
    for kind in KINDS:
        summary[kind]=summary.apply(lambda r: f"{r[kind+': Supports']} / {r[kind+': Contradicts']} / {r[kind+': Unclear']}",axis=1)
    summary["Suggested next step"]=summary.ID.map(lambda i:recommendations[i]['recommendation'])
    visible=[h.id for h in p.hypotheses if (not search or search.lower() in (h.id+" "+h.title+" "+h.statement).lower())
             and (not suggested or recommendations[h.id]["recommendation"] in suggested)
             and (not decisions or summary.set_index("ID").loc[h.id,"Last human decision"].split(" (")[0] in decisions)]
    summary=summary[summary.ID.isin(visible)]
    st.caption(f"{len(visible)} hypotheses · {len(p.customers) if customer_ids is None else len(customer_ids)} customers in scope. Research stays visible.")
    table(summary[["ID","Hypothesis","Suggested next step","Last human decision"]])
    if not visible:
        st.info("No matching hypotheses. Clear or change the filters.")
        return
    hid = st.selectbox("Choose hypothesis", visible, format_func=lambda i:f"{i} · {get(p.hypotheses,i).title}")
    h = get(p.hypotheses,hid)
    st.subheader(h.title)
    st.write(h.statement)
    st.caption(f"Version {h.version} · review by {h.review_on}")
    aa = current_assessments(p,hid,customer_ids)
    recommendation=recommendations[hid]
    with st.container(border=True,key="thesis"):
        st.subheader("Current thesis")
        st.markdown(f"### {recommendation['status']}")
        st.write(recommendation['thesis'])
        st.caption(f"{recommendation['supporting_customers']} supporting · {recommendation['contradicting_customers']} contradicting · {recommendation['mixed_customers']} mixed customers")
        st.write(f"**Suggested next step: {recommendation['recommendation']}.**")
        st.caption("Rule-based draft · subject to your review")
        st.button("Review recommendation",type="primary",on_click=open_recommendation,args=(hid,recommendation))
    with st.expander("Why this recommendation?"):
        st.write(f"Current customer evidence: **{recommendation['supporting_customers']} supporting**, "
                 f"**{recommendation['contradicting_customers']} contradicting**, **{recommendation['mixed_customers']} mixed**.")
        st.write(f"{len(recommendation['stale_sources'])} sources need revalidation; "
                 f"{recommendation['unresolved_mismatches']} unresolved mismatches.")
        st.write("**Next test:**",recommendation['next_test'])
        st.caption("Stronger recommendations require at least 5 customers across 2 cohorts, including 2 with aligned interview and behavior evidence, and a 2:1 directional balance. Mixed findings, unresolved mismatches, or review-due evidence block doubling down or retirement. These are review rules, not statistical confidence.")
        segment_rows=[]
        for stance in ["Supports","Contradicts"]:
            ids={get(p.sources,a.source_id).customer_id for a in aa if a.stance==stance
                 and a.id in recommendation["fresh_assessment_ids"] and get(p.sources,a.source_id).customer_id}
            for segment in sorted({get(p.customers,cid).segment for cid in ids}):
                segment_rows.append({"Segment":segment,"Position":stance,"Customers":sum(get(p.customers,cid).segment==segment for cid in ids)})
        if segment_rows:
            table(segment_rows)
        table(assessment_rows(p,aa))
    st.subheader("Evidence by source")
    table([{"Source":kind,"Supports":int(summary.set_index('ID').loc[hid,kind+': Supports']),
            "Contradicts":int(summary.set_index('ID').loc[hid,kind+': Contradicts']),
            "Unclear":int(summary.set_index('ID').loc[hid,kind+': Unclear'])} for kind in KINDS])
    panels = st.tabs(STANCES)
    for panel, stance in zip(panels,STANCES):
        with panel:
            matching = [a for a in aa if a.stance == stance]
            if matching:
                table(assessment_rows(p,matching))
            else:
                st.caption("No reviewed evidence yet.")
    customers = {get(p.sources,a.source_id).customer_id for a in aa} - {""}
    st.caption(f"{len(customers)} customers · approved links only")
    if aa:
        aid = st.selectbox("View evidence", [a.id for a in aa],format_func=lambda i:f"{get(p.assessments,i).source_id} · {get(p.assessments,i).chunk} · {i}")
        selected = get(p.assessments,aid)
        st.write("**Assessment quotation**")
        st.text(selected.quote)
        with st.expander("Source details"):
            st.write("Limitations:", concise(selected.limitations))
            source_view(p,get(p.sources,selected.source_id),"hypothesis")
    with st.expander("Edit hypothesis"):
        st.caption("Creates a new version and returns non-rejected classifications to review.")
        with st.form(f"hypothesis_edit_{hid}_{h.version}"):
            statement = st.text_area("Hypothesis statement",h.statement)
            author = st.text_input("Revision author")
            if st.form_submit_button("Save new hypothesis version"):
                try:
                    revise_hypothesis(p,hid,statement,author)
                    done("Hypothesis revised. Evidence links need review against the new wording.")
                except ValueError as exc:
                    st.error(str(exc))
        if h.history:
            st.json(h.history,expanded=False)


SOURCE_CATEGORIES={"Initial interview":"Says","Follow-up interview":"Says","Customer feedback review":"Says",
                   "Observed behavior":"Does","External research":"Research","Other":"Says"}


def source_editor(p, s=None):
    identity = f"{s.id}_{s.revision}" if s else "new"
    if s and s.id.startswith("B-"):
        st.info("Edit this action record in Customers.")
        return
    staged = st.session_state.get("staged_document", {}) if not s else {}
    if not s:
        upload = st.file_uploader("Interview or research document",type=["txt","md","pdf","docx"],key="document_upload")
        if st.button("Extract document for review",disabled=upload is None):
            try:
                st.session_state.staged_document = {"name":upload.name,"chunks":extract_document(upload.name,upload.getvalue())}
                done("Document extracted. Preview the passages, complete the metadata, then save the evidence.")
            except Exception as exc:
                st.error(f"Could not read this document: {exc}")
        if staged:
            st.caption(f"Extracted {staged['name']}; {len(staged['chunks'])} passages. Page/paragraph locations are retained.")
            with st.expander("Preview extracted document",expanded=True):
                for label,passage in staged["chunks"].items():
                    st.write(f"**{label}**")
                    st.write(passage)
            st.caption("Extraction fills the passages locally. Save the source, then ask AI to suggest evidence types and hypothesis links for review.")
            if st.button("Discard staged document"):
                st.session_state.pop("staged_document",None)
                done("Staged document discarded.")
    chunks = s.chunks if s else staged.get("chunks",{"Manual note":""})
    location = st.selectbox("Passage to edit",list(chunks),key=f"edit_chunk_{identity}")
    categories=list(SOURCE_CATEGORIES)
    existing_category=getattr(s,"category","Other") if s else "Initial interview"
    category=st.selectbox("Source category",categories,index=categories.index(existing_category) if existing_category in categories else len(categories)-1,key=f"category_{identity}")
    kind=SOURCE_CATEGORIES[category] if category!="Other" else s.kind if s else "Says"
    with st.form(f"source_form_{identity}_{location}"):
        title = st.text_input("Evidence title",concise(s.title) if s else staged.get("name",""))
        st.caption({"Says":"Customer statements","Does":"Observed behavior","Research":"External research"}[kind])
        ids = [""]+[c.id for c in p.customers]
        customer = st.selectbox("Customer (optional)",ids,index=ids.index(s.customer_id) if s else 0)
        text = st.text_area("Source text",chunks[location],height=180)
        url = st.text_input("Original source URL (required for external research)",s.url if s else "") if kind=="Research" else (s.url if s else "")
        with st.expander("Dates & optional notes"):
            left,right=st.columns(2)
            source_date = left.date_input("Source / publication date",s.source_date if s else date.today())
            review_on = right.date_input("Review again on",s.review_on if s else date.today()+timedelta(days=90))
            context = st.text_area("Additional context or limitations (optional)",concise(s.context) if s else "",placeholder="For example: one participant; a different market; interview conducted before the new booking flow.")
            if category=="Other":
                kind=st.selectbox("Evidence type",KINDS,index=KINDS.index(kind))
            version = st.number_input("Product / ICP context version",1,p.context_version,s.context_version if s else p.context_version)
            st.caption("Dates describe when evidence was collected, not when it was uploaded.")
        synthetic = s.synthetic if s and s.kind == kind else kind != "Research"
        save = st.form_submit_button("Save evidence changes" if s else "Add evidence",type="primary")
    if save:
        try:
            values = dict(title=title,kind=kind,category=category,customer_id=customer,chunks={**chunks,location:text},source_date=source_date,
                review_on=review_on,url=url,context=context,synthetic=synthetic,context_version=int(version))
            if s:
                values.update(expected_action="",expected_by=None,expectation_quote="",expectation_reviewer="")
                edit_source(p,s.id,values)
            else:
                created=Source(id=uid("E"),**values)
                p.sources.append(created)
                st.session_state.selected_evidence=created.id
                st.session_state.evidence_search=""
                st.session_state.pop("staged_document",None)
            done("Source updated; linked classifications need review." if s else "Source added and selected below. Next: suggest links with AI or select a passage to link manually.")
        except ValueError as exc:
            st.error(str(exc))


def expectation_form(p,s):
    if s.kind != "Says" or not s.customer_id:
        return
    with st.expander("Expected action"):
        st.caption("A reviewer verifies an exact statement and deadline. Unknown and not-applicable actions are never failures.")
        with st.form(f"expect_{s.id}_{s.revision}"):
            actions=[""]+list(ACTIONS)
            action=st.selectbox("Expected action",actions,index=actions.index(s.expected_action))
            quote=st.text_area("Exact statement of intent",s.expectation_quote)
            deadline=st.date_input("Expected by",s.expected_by or max(date.today(),s.source_date))
            reviewer=st.text_input("Expectation reviewer",s.expectation_reviewer)
            if st.form_submit_button("Save action expectation"):
                try:
                    edit_source(p,s.id,dict(expected_action=action,expected_by=deadline if action else None,
                        expectation_quote=quote if action else "",expectation_reviewer=reviewer if action else ""))
                    done("Expectation saved. Linked classifications need review for the new source revision.")
                except ValueError as exc:
                    st.error(str(exc))


def classify(p,s):
    st.subheader("Connect this source to a hypothesis")
    st.caption("Choose AI suggestions or add a link yourself. Both create drafts for review below.")
    with st.expander("Link to a hypothesis"):
        location=st.selectbox("Passage to link",list(s.chunks),key=f"link_passage_{s.id}_{s.revision}")
        passage=s.chunks[location]
        st.write(passage)
        shorter=st.checkbox("Use a shorter excerpt",key=f"short_quote_{s.id}_{s.revision}")
        with st.form(f"classify_{s.id}_{s.revision}_{location}"):
            hid=st.selectbox("Hypothesis",[h.id for h in p.hypotheses],format_func=lambda i:f"{i} · {get(p.hypotheses,i).title}")
            quote=st.text_area("Exact quotation",value=passage,help="Keep an exact excerpt from the source.") if shorter else passage
            stance=st.selectbox("Proposed position",STANCES)
            rationale=st.text_area("Why this position?",placeholder="One sentence explaining how this passage relates to the selected hypothesis.")
            with st.expander("Optional caveats"):
                limits=st.text_area("Limitations (optional)",placeholder="Add only if this link needs a qualification.")
            if st.form_submit_button("Save proposed link"):
                try:
                    new_link=add_assessment(p,s.id,hid,location,quote,stance,rationale,limits)
                    st.session_state[f"review_link_{s.id}"]=new_link.id
                    done("Draft link created. Verify the quotation and approve, edit or reject it below.")
                except ValueError as exc:
                    st.error(str(exc))
    with st.expander("AI suggestions"):
        enabled,key,model=ai_config()
        if analysis_mode()!="OpenAI":
            st.caption("Use AI analysis for demo scenarios or local Ollama; select your source there.")
            st.button("Open workspace analysis",on_click=navigate,args=("AI analysis",))
            return
        st.caption("AI proposes passage types and hypothesis links, with quotations filled in. Selected text, category, optional notes, ICP and hypotheses go to OpenAI only when you click Analyze. Every proposal needs your approval.")
        if not enabled or not key:
            st.info("Connect an API key to generate suggestions.")
        st.button("Open AI setup",on_click=navigate,args=("AI setup",))
        passages=st.multiselect("Passages to analyze",list(s.chunks),default=list(s.chunks) if sum(map(len,s.chunks.values()))<=24000 else list(s.chunks)[:1],key=f"ai_chunks_{s.id}_{s.revision}")
        consent=st.checkbox("Send these selected passages for AI analysis",key=f"ai_consent_{s.id}_{s.revision}")
        attempts=st.session_state.get("ai_attempts",0)
        st.caption(f"Model: {model}. Up to 10 attempts per session; 24,000 characters per request.")
        if st.button("Analyze selected evidence",disabled=not(enabled and key and consent and passages) or attempts>=10):
            st.session_state.ai_attempts=attempts+1
            try:
                with st.spinner("Proposing links with source quotations…"):
                    proposals=ai_proposals(p,s.id,passages,key,model)
                    count=accept_proposals(p,s.id,proposals,f"OpenAI / {model} / prompt v1")
                done(f"{count} new proposals saved for review. {proposals.note}")
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("AI request failed. Check model access, credentials, quota, or connectivity. No decision was changed; manual review remains available.")


def cite_reviewed_link(a):
    st.session_state.workspace="Decisions"
    st.session_state.decision_hypothesis=a.hypothesis_id
    st.session_state.pop("decision_draft",None)
    st.session_state[f"decision_cites_{a.hypothesis_id}"]=[a.id]


def open_review_source(source_id):
    st.session_state.workspace="Evidence"
    st.session_state.selected_evidence=source_id


def review_queue(p,s):
    aa=[a for a in p.assessments if a.source_id==s.id]
    st.subheader("Review suggested links")
    st.caption("Check the quotation against the source, confirm its relationship to the hypothesis, then save your review. Approval verifies this link—not the hypothesis itself.")
    if not aa:
        st.info("No links proposed yet. Add one manually or use optional AI analysis.")
        return
    table(assessment_rows(p,aa))
    aid=st.selectbox("Choose link",[a.id for a in aa],key=f"review_link_{s.id}",format_func=lambda i:f"{get(p.assessments,i).hypothesis_id} · {i}")
    a=get(p.assessments,aid)
    h=get(p.hypotheses,a.hypothesis_id)
    st.write(f"**{h.id}: {h.statement}**")
    st.caption(f"Status: {a.status} · Proposed by {a.origin} · Source revision {a.source_revision}; current revision {s.revision}")
    with st.expander("Compare with the source",expanded=a.status in ("Pending","Needs review")):
        left,right=st.columns(2)
        left.write("**Original source passage**")
        left.write(s.chunks.get(a.chunk,"The original passage changed. Choose a current passage below."))
        right.write("**Proposed quotation**")
        right.write(a.quote)
        right.caption("Supports = directly backs this claim. Contradicts = directly challenges it. Unclear = insufficient, indirect or mixed evidence.")
    chunk=st.selectbox("Reviewed passage location",list(s.chunks),index=list(s.chunks).index(a.chunk) if a.chunk in s.chunks else 0,key=f"review_passage_{aid}_{s.revision}")
    with st.form(f"review_{aid}_{s.revision}_{h.version}_{len(a.reviews)}"):
        reviewed_kind=st.selectbox("Passage evidence type",KINDS,index=KINDS.index(assessment_kind(p,a)),help="Says: direct customer account. Does: observed behavior. Research: external evidence. Research quotations remain Research.")
        stance=st.selectbox("Reviewed position",STANCES,index=STANCES.index(a.stance))
        with st.expander("Edit quotation or caveats"):
            quote=st.text_area("Reviewed exact quotation",a.quote if chunk==a.chunk else s.chunks[chunk])
            limits=st.text_area("Reviewed limitations",concise(a.limitations))
        rationale=st.text_area("Reviewed rationale",concise(a.rationale))
        reviewer=st.text_input("Reviewer name")
        status=st.radio("Review outcome",["Approved","Pending","Rejected"],horizontal=True,help="Approved: usable in triangulation and decisions. Pending: leave for later. Rejected: exclude this proposed link.")
        if st.form_submit_button("Save classification review",type="primary"):
            try:
                review_assessment(p,aid,stance,quote,chunk,rationale,limits,status,reviewer,reviewed_kind)
                st.session_state.last_reviewed_link=aid
                done(f"{status} review saved for {a.hypothesis_id}. " + ("It is ready to cite: use the decision button below." if status=="Approved" else "This link is not included in decision citations."))
            except ValueError as exc:
                st.error(str(exc))
    if any(link.id==aid for link in current_assessments(p)):
        st.success("Approved link · available in Decisions")
        st.button("Use this evidence in a decision",on_click=cite_reviewed_link,args=(a,),key=f"cite_{aid}")
        if freshness(p,s,a.hypothesis_id)!="Current":
            st.caption("This source needs a freshness review. Approval does not reset its age or product/ICP context.")
    with st.expander("Review history",expanded=st.session_state.get("last_reviewed_link")==aid):
        history=[r for r in review_history_rows(p,s.id) if r["Link"]==aid]
        if history:
            table(history)
        else:
            st.caption("No reviews saved for this link yet.")
        with st.expander("Original proposal & full audit"):
            current=get(p.assessments,aid)
            st.json({"original":current.original,"reviews":current.reviews},expanded=False)


def evidence_page(p):
    st.header("Evidence")
    workspace_findings(p,"Evidence")
    st.caption("Add a source → review its hypothesis links → use approved evidence in a decision. Each link says what one passage supports, contradicts or leaves unclear.")
    with st.expander("Recent reviews",expanded=bool(st.session_state.get("last_reviewed_link"))):
        history=review_history_rows(p)
        if history:
            table(history[:25])
            st.caption("Latest 25 reviews across all sources, including those hidden by library filters. Full history is retained on each link.")
        else:
            st.caption("No classification reviews yet.")
    with st.expander("Add a source — upload or paste"):
        source_editor(p)
    with st.container():
        left,right=st.columns([2,1])
        query=left.text_input("Find evidence",key="evidence_search",placeholder="Title, source ID, customer ID, or source text")
        order=right.selectbox("Sort evidence",["Newest added","Oldest added","Newest source date","Oldest source date","Most passages","Source ID"])
        with st.expander("Archived evidence"):
            show_archived=st.checkbox("Include archived evidence")
        sources=[source for source in p.sources if (show_archived or not source.archived)
                 and (not query or query.lower() in (source.id+source.title+source.customer_id+" ".join(source.chunks.values())).lower())]
        added={source.id:index for index,source in enumerate(p.sources)}
        if order in ("Newest added","Oldest added"):
            sources.sort(key=lambda source:added[source.id],reverse=order=="Newest added")
        elif order in ("Newest source date","Oldest source date"):
            sources.sort(key=lambda source:(source.source_date,added[source.id]),reverse=order=="Newest source date")
        elif order=="Most passages":
            sources.sort(key=lambda source:(-len(source.chunks),source.id))
        else:
            sources.sort(key=lambda source:source.id)
        st.caption(f"{len(sources)} sources")
        table([{"ID":s.id,"Title":concise(s.title),"Type":s.kind,"Customer":s.customer_id,"Source date":s.source_date,
                "Passages":len(s.chunks),"Review on":s.review_on,"Freshness":freshness(p,s),"Archived":s.archived} for s in sources])
        if not sources:
            st.info("No matches. Clear the search or add evidence.")
            return
        sid=st.selectbox("Choose evidence",[s.id for s in sources],key="selected_evidence",format_func=lambda i:f"{i} · {concise(get(p.sources,i).title)} · {len(get(p.sources,i).chunks)} passages")
        s=get(p.sources,sid)
        source_view(p,s,"evidence")
        if s.archived:
            if st.button("Restore evidence"):
                edit_source(p,sid,{"archived":False})
                done("Evidence restored; classifications need review.")
            return
        classify(p,s)
        review_queue(p,s)
        with st.expander("Edit evidence"):
            source_editor(p,s)
        with st.expander("Freshness"):
            with st.form(f"freshness_{s.id}_{s.revision}"):
                next_date=st.date_input("Next evidence review",max(date.today()+timedelta(days=90),s.review_on))
                applicable=st.checkbox("I reviewed applicability to the current product / ICP context")
                reason=st.text_area("Freshness review rationale")
                reviewer=st.text_input("Freshness reviewer")
                if st.form_submit_button("Save freshness review"):
                    if not reviewer.strip() or not reason.strip() or next_date<=date.today():
                        st.error("Provide a reviewer, rationale, and a future review date.")
                    else:
                        edit_source(p,s.id,{"review_on":next_date,
                            "context_version":p.context_version if applicable else s.context_version,
                            "context_reviews":s.context_reviews+[{"at":now(),"reviewer":reviewer,"rationale":reason,
                                "context_version":p.context_version,"applicable":applicable}]})
                        done("Freshness review recorded. Reapprove evidence classifications for this revision.")
            if s.context_reviews:
                st.json(s.context_reviews,expanded=False)
        expectation_form(p,s)
        with st.expander("Archive evidence"):
            st.caption("Archived evidence leaves active summaries but remains in project history.")
            if st.button("Archive this source"):
                edit_source(p,sid,{"archived":True})
                done("Source archived. Its history remains in the project.")


def customers_page(p):
    st.header("Customers")
    workspace_findings(p,"Customers")
    st.caption("Record who paid and what they did. Customer actions become evidence; interviews and research are added in Evidence.")
    tools=st.columns(4)
    with tools[0].popover("Add / edit",icon=":material/edit:",width="stretch"):
        choice=st.selectbox("Customer to edit",["New customer"]+[c.id for c in p.customers])
        c=get(p.customers,choice) if choice!="New customer" else None
        with st.form(f"customer_{choice}"):
            left,right=st.columns(2)
            cid=left.text_input("Customer ID",c.id if c else f"DEMO-{max([x.number for x in p.customers] or [0])+1:03d}",disabled=c is not None)
            number=right.number_input("Acquisition number",1,value=c.number if c else max([x.number for x in p.customers] or [0])+1)
            age=left.number_input("Age",18,100,c.age if c else 28)
            segment=right.text_input("Segment",c.segment if c else "Young professional / health concern")
            channel=left.text_input("Acquisition channel",c.channel if c else "Personal outreach")
            trigger=right.text_input("Purchase trigger",c.trigger if c else "Wanted clear next steps")
            purchased=left.date_input("Purchased on",c.purchased_on if c else date.today())
            observed=right.date_input("Observed through",c.observed_through if c else date.today())
            discount=left.number_input("Discount (%)",0,100,c.discount if c else 0)
            satisfaction=right.number_input("Satisfaction (1–5)",1,5,c.satisfaction if c else 4)
            note=st.text_area("Customer note",(concise(c.note) or "Customer record.") if c else "Customer note.")
            event_rows=[{"Action":a,"Status":c.events[a].status if c else ("Completed" if a=="baseline_purchased" else "Unknown"),
                         "Date":c.events[a].on if c else (date.today() if a=="baseline_purchased" else None)} for a in ACTIONS]
            edited=st.data_editor(pd.DataFrame(event_rows),hide_index=True,width="stretch",disabled=["Action"],
                column_config={"Status":st.column_config.SelectboxColumn(options=EVENT_STATES,required=True),
                    "Date":st.column_config.DateColumn(format="YYYY-MM-DD")},key=f"events_{choice}")
            st.caption("Dates are required only for completed actions. Use Unknown for missing observations; Not applicable for inappropriate or unavailable actions.")
            if st.form_submit_button("Save customer"):
                try:
                    events={r["Action"]:Event(status=r["Status"],on=None if pd.isna(r["Date"]) else r["Date"]) for r in edited.to_dict("records")}
                    events["baseline_purchased"]=Event(status="Completed",on=purchased)
                    customer=Customer(id=cid,number=int(number),age=int(age),segment=segment,channel=channel,trigger=trigger,
                        purchased_on=purchased,observed_through=observed,discount=int(discount),satisfaction=int(satisfaction),note=note,events=events)
                    save_customers(p,[customer],replace_existing=c is not None)
                    done("Customer saved and behavioral evidence updated.")
                except ValueError as exc:
                    st.error(str(exc))
    with tools[1].popover("Upload CSV",icon=":material/upload_file:",width="stretch"):
        st.download_button("Download customer CSV template",customer_frame(p.customers).to_csv(index=False),"alaga_synthetic_customers.csv","text/csv")
        upload=st.file_uploader("Customer CSV",type="csv")
        mode=st.radio("Matching IDs",["Reject duplicates","Update matching IDs"],horizontal=True)
        if upload:
            try:
                if upload.size>5_000_000:
                    raise ValueError("CSV exceeds 5 MB.")
                incoming=parse_customers(pd.read_csv(BytesIO(upload.getvalue())))
                st.caption(f"Preview: {len(incoming)} records. Existing customers omitted from the CSV remain in the project.")
                table(customer_frame(incoming).head(10))
                if st.button("Apply customer CSV"):
                    save_customers(p,incoming,replace_existing=mode=="Update matching IDs")
                    done("Customer CSV applied and behavioral sources updated.")
            except (ValueError,UnicodeError) as exc:
                st.error(str(exc))
    with tools[2].popover("Scoring",icon=":material/tune:",width="stretch"):
        weights={a:st.number_input(a.replace("_"," ").capitalize(),0,20,w,key=f"weight_{a}") for a,w in ACTIONS.items() if w}
        cutoff=st.number_input("Power-user score cutoff",0,value=7)
        st.caption("Illustrative score: completed actions once within 30 days of purchase. Review satisfaction and appropriate return use before interpreting activity as customer value.")
    rows=[]
    for c in p.customers:
        score=sum(w for a,w in weights.items() if c.events[a].status=="Completed" and (c.events[a].on-c.purchased_on).days<=30)
        row={"ID":c.id,"Age":c.age,"Segment":c.segment,"Channel":c.channel,"Cohort":"1–10" if c.number<=10 else "11–30" if c.number<=30 else "31–100" if c.number<=100 else "101+",
             "Score":score,"Power user":score>=cutoff,"Satisfaction":c.satisfaction,
             "30-day window complete":(c.observed_through-c.purchased_on).days>=30}
        for a,window in [("return_30_day",30),("return_90_day",90),("successful_referral",0)]:
            e=c.events[a]
            eligible=e.status in ("Completed","Not completed") and (window==0 or (c.observed_through-c.purchased_on).days>=window)
            row[a]=int(e.status=="Completed") if eligible else None
        rows.append(row)
    frame=pd.DataFrame(rows)
    if frame.empty:
        st.info("Add a customer to start.")
        return
    order=st.selectbox("Sort customers",["Newest added","Oldest added","Newest purchase","Oldest purchase","Highest score","Customer ID"])
    with tools[3].popover("Filters",icon=":material/filter_list:",width="stretch"):
        left,middle,right=st.columns(3)
        for col,widget in [("Segment",left),("Channel",middle),("Cohort",right)]:
            selected=widget.multiselect(col,sorted(frame[col].unique(), key=lambda value: int(value.split("–")[0].rstrip("+"))) if col=="Cohort" else sorted(frame[col].unique()))
            if selected:
                frame=frame[frame[col].isin(selected)]
        search=st.text_input("Find customer",placeholder="Customer ID, purchase trigger or note")
        power=st.selectbox("Power-user status",["All","Power users","Other customers"])
        scores=st.slider("Score range",0,max(1,sum(weights.values())),(0,max(1,sum(weights.values()))))
        ages=st.slider("Age range",18,100,(18,100))
        satisfaction=st.slider("Minimum satisfaction",1,5,1)
        returned=st.selectbox("30-day return",["All","Returned","Did not return","Not yet measurable"])
    if search:
        matching={c.id for c in p.customers if search.lower() in (c.id+" "+c.trigger+" "+c.note).lower()}
        frame=frame[frame.ID.isin(matching)]
    frame=frame[frame.Score.between(*scores) & frame.Age.between(*ages) & (frame.Satisfaction>=satisfaction)]
    if power!="All":
        frame=frame[frame["Power user"]==(power=="Power users")]
    if returned!="All":
        frame=frame[frame["return_30_day"].isna()] if returned=="Not yet measurable" else frame[frame["return_30_day"]==(1 if returned=="Returned" else 0)]
    if order in ("Newest added","Oldest added"):
        added={c.id:i for i,c in enumerate(p.customers)}
        frame=frame.sort_values("ID",key=lambda ids:ids.map(added),ascending=order=="Oldest added",kind="stable")
    elif order in ("Newest purchase","Oldest purchase"):
        dates={c.id:c.purchased_on for c in p.customers}
        frame=frame.sort_values("ID",key=lambda ids:ids.map(dates),ascending=order=="Oldest purchase",kind="stable")
    else:
        frame=frame.sort_values("Score" if order=="Highest score" else "ID",ascending=order!="Highest score",kind="stable")
    st.caption(f"{len(frame)} customers in view; {int(frame['Power user'].sum())} meet the illustrative score cutoff. ")
    if not frame["30-day window complete"].all():
        st.caption("Some scores are provisional: these customers have not completed their first 30-day observation window. Compare mature windows before drawing segment conclusions.")
    table(frame)
    if not frame.empty:
        inspected=st.selectbox("Choose customer",frame["ID"].tolist())
        customer=get(p.customers,inspected)
        with st.expander("Actions & score"):
            table([{"Action":a,"Status":e.status,"Date":e.on,"Weight":weights.get(a,0),
                "Points":weights.get(a,0) if e.status=="Completed" and (e.on-customer.purchased_on).days<=30 else 0}
                for a,e in customer.events.items()])
            st.write(concise(customer.note))
        st.subheader("Segment and cohort comparisons")
        group=st.radio("Group by",["Segment","Channel","Cohort"],horizontal=True)
        comparison=frame.groupby(group,dropna=False).agg(Customers=("ID","size"),Power_user_rate=("Power user","mean"),
            Average_score=("Score","mean"),Return_30_rate=("return_30_day","mean"),Return_30_eligible=("return_30_day","count"),
            Return_90_rate=("return_90_day","mean"),Return_90_eligible=("return_90_day","count"),Referral_rate=("successful_referral","mean"),Referral_eligible=("successful_referral","count")).reset_index()
        if group=="Cohort":
            comparison=comparison.sort_values("Cohort",key=lambda col:col.map(lambda value:int(value.split("–")[0].rstrip("+"))))
        table(comparison.round(2).rename(columns=lambda name:name.replace("_"," ")))
        st.caption("Rates are fractions (0–1). Returns include only full observation windows with known applicable results; eligible counts are shown. Missing rates mean no eligible observations.")


def contradictions_page(p):
    st.header("Contradictions")
    workspace_findings(p,"Contradictions")
    st.write("Review differences between customer statements and actions.")
    rows=contradictions(p)
    if not rows:
        st.info("No mismatches flagged.")
        return
    table([{k:v for k,v in r.items() if k not in ("id","sources")} for r in rows])
    key=st.selectbox("Choose mismatch",[r["id"] for r in rows],format_func=lambda i:next(f"{r['customer']} · {r['type']} · {r['hypothesis']}" for r in rows if r["id"]==i))
    row=next(r for r in rows if r["id"]==key)
    st.write(row["detail"])
    for col,sid in zip(st.columns(2),row["sources"]):
        with col:
            source_view(p,get(p.sources,sid),"contradiction_"+sid)
    st.caption("Consider price, booking access, changed needs, or an inappropriate action. Intention checks require an explicit quoted deadline and observations through that deadline. Opposing-link checks require approved Says/Does links for the same customer and hypothesis within 90 days and the same context version.")
    with st.form(f"resolve_{key}"):
        status=st.selectbox("Mismatch review outcome",["Open","Confirmed mismatch","Explained / dismissed"])
        explanation=st.text_area("Explanation or next question")
        reviewer=st.text_input("Mismatch reviewer")
        if st.form_submit_button("Save mismatch review"):
            if not explanation.strip() or not reviewer.strip():
                st.error("Add an explanation and reviewer.")
            else:
                p.contradiction_reviews.setdefault(key,[]).append(dict(status=status,explanation=explanation,reviewer=reviewer,at=now()))
                done("Mismatch review saved. No strategic decision was changed.")
    with st.expander("Mismatch review history"):
        st.json(p.contradiction_reviews.get(key,[]),expanded=False)


def decisions_page(p):
    st.header("Decisions")
    workspace_findings(p,"Decisions")
    st.caption("Record a human decision: choose a hypothesis, cite approved links, explain your reasoning and define the next test.")
    flagged=[s for s in p.sources if not s.archived and freshness(p,s)!="Current"]
    table([{"ID":s.id,"Source":s.title,"Source date":s.source_date,"Review on":s.review_on,"Status":freshness(p,s)} for s in flagged])
    if not flagged:
        st.info("No sources need a freshness review.")
    with st.expander("Log a product / ICP change"):
        st.caption("Use this when the product, offer or target customer changes enough that earlier evidence may no longer apply. This flags evidence; it does not approve or reject it.")
        with st.form("context_change"):
            change_type=st.selectbox("Change type",["Product / service","Target customer (ICP)","Price / offer","Other context"])
            description=st.text_area("What changed, and which earlier findings might no longer apply?",
                placeholder="Product v2: we added evening blood-draw appointments. Earlier interviews describing work-hour booking barriers may no longer apply to H6.\n\nICP: we now target shift workers rather than all young professionals. Recheck whether earlier convenience and guidance findings transfer to this group.")
            affected=st.multiselect("Hypotheses to revalidate",[h.id for h in p.hypotheses],format_func=lambda i:f"{i} · {get(p.hypotheses,i).title}")
            on=st.date_input("Effective date",date.today())
            icp=st.text_area("Current ICP wording",p.icp)
            author=st.text_input("Change author")
            if st.form_submit_button("Log change and flag evidence"):
                try:
                    if on>date.today() or not icp.strip():
                        raise ValueError("Log changes already in effect and provide the ICP wording.")
                    change=Change(id=uid("CH"),version=p.context_version+1,on=on,description=f"{change_type}: {description}" if description.strip() else "",hypotheses=affected,author=author)
                    p.changes.append(change)
                    p.context_version=change.version
                    p.icp=icp
                    done("Change logged. Earlier evidence for affected hypotheses is flagged for revalidation.")
                except ValueError as exc:
                    st.error(str(exc))
    st.subheader("Your decision")
    hid=st.selectbox("Decision hypothesis",[h.id for h in p.hypotheses],key="decision_hypothesis")
    h=get(p.hypotheses,hid)
    aa=current_assessments(p,hid)
    draft=st.session_state.get("decision_draft",{})
    if draft.get("hypothesis_id") != hid:
        draft={}
    if draft:
        scope=draft.get("customer_scope","All customers")
        draft=hypothesis_thesis(p,hid,None if scope=="All customers" else set(scope))
        st.info(f"Draft recommendation: {draft['recommendation']}. Edit the decision below before saving.")
    st.write(f"**{h.title}** — {h.statement}")
    pending=[a for a in p.assessments if a.hypothesis_id==hid and a.status in ("Pending","Needs review") and not get(p.sources,a.source_id).archived]
    st.caption(f"{len(aa)} approved links available to cite · {len(pending)} awaiting review")
    if pending:
        st.button("Review waiting evidence",on_click=open_review_source,args=(pending[0].source_id,))
    if not aa:
        st.info("No approved links for this hypothesis yet. In Evidence, propose a link, verify the quotation and save an Approved review.")
    citation_key=f"decision_cites_{hid}"
    options=[a.id for a in aa]
    if citation_key in st.session_state:
        st.session_state[citation_key]=[i for i in st.session_state[citation_key] if i in options]
    else:
        st.session_state[citation_key]=[i for i in draft.get("assessment_ids",[]) if i in options]
    cited=st.multiselect("Cite reviewed assessments",options,key=citation_key,
        format_func=lambda i:f"{concise(get(p.sources,get(p.assessments,i).source_id).title)} · {get(p.assessments,i).stance} · {get(p.assessments,i).chunk} · {i}",
        help="Only approved links with valid quotations and current source/hypothesis revisions appear. Freshness is shown in the preview.")
    if cited:
        table([{ "Source":concise(get(p.sources,a.source_id).title),"Position":a.stance,
                 "Quotation":a.quote,"Freshness":freshness(p,get(p.sources,a.source_id),hid),
                 "Reviewed by":a.reviews[-1]["reviewer"] if a.reviews else "—"} for a in aa if a.id in cited])
    actions=["Keep testing","Double down","Revise","Retire"]
    with st.form(f"decision_{hid}"):
        action=st.selectbox("Strategic decision",actions,index=actions.index(draft.get("action","Keep testing")))
        rationale=st.text_area("Decision rationale",draft.get("thesis",""))
        next_test=st.text_area("Next test / evidence to collect",draft.get("next_test",""))
        reviewer=st.text_input("Decision author")
        review_on=st.date_input("Next hypothesis review",date.today()+timedelta(days=30))
        if st.form_submit_button("Save human decision",type="primary"):
            try:
                if action!="Keep testing" and not cited:
                    raise ValueError("Cite reviewed evidence before doubling down, revising, or retiring.")
                if review_on<date.today():
                    raise ValueError("Next review cannot be in the past.")
                d=Decision(id=uid("D"),hypothesis_id=hid,hypothesis_version=h.version,context_version=p.context_version,
                    action=action,rationale=rationale,next_test=next_test,assessment_ids=cited,author=reviewer,created_at=now(),
                    evidence_snapshot=[get(p.assessments,i).model_dump(mode="json") for i in cited],
                    recommendation_snapshot=draft)
                p.decisions.append(d)
                h.review_on=review_on
                st.session_state.pop("decision_draft",None)
                done("Human decision recorded. Source freshness flags remain until their context is reviewed.")
            except ValueError as exc:
                st.error(str(exc))
    st.subheader("Decision history")
    for d in reversed(p.decisions):
        with st.expander(f"{d.hypothesis_id} · {d.action} · {d.author} · {d.created_at}"):
            st.write(d.rationale)
            st.write("Next test:",d.next_test)
            if d.recommendation_snapshot:
                st.write("Suggested at review:",d.recommendation_snapshot["recommendation"])
            st.caption(f"Hypothesis version {d.hypothesis_version}; context version {d.context_version}")
            table(assessment_rows(p,[get(p.assessments,i) for i in d.assessment_ids]))
            st.write("Evidence as reviewed at decision time:")
            st.json(d.evidence_snapshot,expanded=False)
            changed=any(get(p.assessments,i).status!="Approved" for i in d.assessment_ids)
            changed=changed or any(get(p.assessments,a['id']).model_dump(mode="json")!=a for a in d.evidence_snapshot)
            if changed or d.hypothesis_version!=get(p.hypotheses,d.hypothesis_id).version:
                st.warning("Some cited classifications changed or need review. This historical decision has not been rewritten.")
    with st.expander("Change history"):
        st.json([c.model_dump(mode="json") for c in p.changes],expanded=False)


def ask_data_page(p):
    from data_workbench import workbench_page
    enabled,key,model=ai_config()
    workbench_page(p,analysis_mode(),model,key,enabled)


def main():
    st.set_page_config(page_title="Alaga Evidence Review",layout="wide",initial_sidebar_state="collapsed")
    st.markdown("""<style>
    .block-container {padding-top:3.5rem; max-width:1100px; margin-left:auto; margin-right:auto;}
    [data-testid="stMain"] {width:100%; margin-left:0 !important; transition:filter 160ms ease;}
    [data-testid="stSidebar"] {position:fixed !important; top:0; bottom:0; left:0; z-index:1001;}
    [data-testid="stSidebar"][aria-expanded="true"] {box-shadow:4px 0 8px rgba(0,0,0,.3);}
    [data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="true"]) [data-testid="stMain"] {filter:blur(2px) brightness(.65);}
    [data-testid="stHeader"] {z-index:1000;}
    [data-testid="stSidebarCollapseButton"] {visibility:visible !important;}
    h1 {font-size:2rem !important;} h2 {font-size:1.5rem !important;}
    h3 {font-size:1.2rem !important;} button {border-radius:6px !important;}
    .st-key-thesis {background:var(--secondary-background-color); border:1px solid var(--primary-color) !important;
        padding:24px 28px !important; margin:8px 0 20px;}
    .st-key-thesis h3 {font-size:1.6rem !important;}
    .st-key-thesis p {font-size:1.08rem; line-height:1.6;}
    [data-testid="stSidebar"] {min-width:240px; max-width:260px; border-right:1px solid color-mix(in srgb, var(--text-color) 18%, transparent);}
    .st-key-workspace [role="radiogroup"] {gap:4px;}
    .st-key-workspace label {padding:10px 12px; margin:0 !important; width:100%; border-radius:4px;
        transition:background-color 160ms ease;}
    .st-key-workspace label:has(input:checked) {background:color-mix(in srgb, var(--primary-color) 18%, transparent);}
    .st-key-workspace label:hover {background:color-mix(in srgb, var(--text-color) 8%, transparent);}
    .st-key-workspace label:focus-within {outline:2px solid var(--primary-color); outline-offset:-2px;}
    [data-testid="stExpander"] details {transition:background-color 160ms ease,border-color 160ms ease;}
    [data-testid="stExpander"] summary {padding:14px 16px; font-weight:600;}
    [data-testid="stExpander"] details:hover {border-color:#89ac9e;}
    @keyframes reveal {from {opacity:0.4;} to {opacity:1;}}
    .st-key-thesis {animation:reveal 220ms ease-out;}
    @media (prefers-reduced-motion:reduce) {
        .st-key-thesis {animation:none;}
        [data-testid="stMain"] {transition:none;}
        .st-key-workspace label, [data-testid="stExpander"] details {transition:none;}
    }
    @media (max-width:700px) {
        .st-key-workspace label {padding:10px 12px;}
        .st-key-thesis {padding:18px !important;}
    }
    </style>""",unsafe_allow_html=True)
    if "project" not in st.session_state:
        st.session_state.project=load_demo()
    if not hasattr(st.session_state.project,"ai_report"):
        st.session_state.project=Project.model_validate(st.session_state.project.model_dump())
    p=st.session_state.project
    # Upgrade only the prepared report, preserving all source/review/decision data.
    # No local or cloud model is called by this migration.
    if p.ai_report.get("provider")=="Demo scenarios" and p.ai_report.get("summary_version",0)<2:
        from local_ai import DemoClient
        p=analyze_workspace(p,"demo","Prepared scenarios v1",client=DemoClient(),provider="Demo scenarios")
        st.session_state.project=p
    for setting in ("workspace_ai_auto","workspace_ai_consent"):
        st.session_state[setting]=st.session_state.get(setting,False)
    st.session_state.analysis_mode=analysis_mode()
    for setting in ("ollama_model","local_source_ids","local_all_sources"):
        if setting in st.session_state: st.session_state[setting]=st.session_state[setting]
    st.title("Alaga Evidence Review")
    st.caption("Demo data · Understand who values Alaga, test why, and decide what to do next.")
    with st.expander("How to use this workspace"):
        st.write("**Dashboard** shows usage and growth. **Customers** records who bought and what they did. **Evidence** turns interviews, feedback and research into reviewed links. **Hypotheses** weighs those links for and against each claim. **Contradictions** highlights statements that disagree with actions. **Decisions** records your conclusion, cited evidence and next test.")
        st.write("Start with a question in Hypotheses, add what you learned in Evidence, approve relevant links, then record your next move in Decisions. AI analysis offers prepared demo scenarios, local Ollama, and optional OpenAI. Only OpenAI needs an API account. Enable automatic updates for demo or OpenAI mode. AI findings use the full customer base; reviewed evidence still controls the rule-based thesis and decision citations.")
    if "notice" in st.session_state:
        st.success(st.session_state.pop("notice"))
    page=st.sidebar.radio("Workspace",["Dashboard","Hypotheses","Evidence","Customers","Contradictions","Decisions","Ask your data","AI analysis","AI setup"],key="workspace",label_visibility="collapsed")
    with st.sidebar.expander("Project"):
        st.write("Export your project to keep sources, reviews, decisions and activity between sessions.")
        st.caption("Export to save your work before leaving.")
        st.download_button("Export project",p.model_dump_json(indent=2),"alaga_evidence_project.json","application/json")
        upload=st.file_uploader("Restore exported project",type="json")
        if st.button("Import project",disabled=upload is None):
            try:
                candidate=import_project(upload.getvalue())
                st.session_state.project=candidate
                for key in list(st.session_state):
                    if key not in ("project","ai_attempts"):
                        del st.session_state[key]
                done("Project imported. Evidence and review history restored.")
            except ValueError as exc:
                st.error(f"Project rejected; current work retained. {exc}")
        reset=st.checkbox("Discard session edits and restore the bundled demo")
        if st.button("Reset demo",disabled=not reset):
            attempts=st.session_state.get("ai_attempts",0)
            st.session_state.clear()
            st.session_state.ai_attempts=attempts
            done("Bundled demo restored.")
    enabled,api_key,model=ai_config()
    report=getattr(p,"ai_report",{}) or {}
    input_hash=fingerprint(p)
    if (st.session_state.get("workspace_ai_auto") and (analysis_mode()=="Demo scenarios" or st.session_state.get("workspace_ai_consent"))
        and analysis_mode()!="Local Ollama"
        and enabled and api_key and report and (report.get("input_hash")!=input_hash or report.get("provider","OpenAI")!=analysis_mode())
        and st.session_state.get("ai_last_attempt")!=input_hash+analysis_mode()+model):
        p=run_workspace_ai(p)
    st.sidebar.caption("Appearance: ⋮ → Theme → Light or Dark")
    {"Dashboard":dashboard_page,"Hypotheses":hypotheses_page,"Evidence":evidence_page,"Customers":customers_page,
     "Contradictions":contradictions_page,"Decisions":decisions_page,"AI setup":ai_setup_page,"AI analysis":ai_analysis_page,"Ask your data":ask_data_page}[page](p)


if __name__=="__main__":
    main()
