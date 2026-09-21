"""Business activity metrics from dated events, never inferred from purchases."""
from datetime import timedelta
import pandas as pd


def cohort(number):
    return "1–10" if number<=10 else "11–30" if number<=30 else "31–100" if number<=100 else "101+"


def activity_report(p, as_of, customer_ids=None):
    start,end=getattr(p,"activity_start",None),getattr(p,"activity_end",None)
    if not start or not end or not start<=as_of<=end:
        raise ValueError("Choose an as-of date within recorded activity coverage.")
    ids={c.id for c in p.customers if c.purchased_on<=as_of}
    if customer_ids is not None:
        ids &= set(customer_ids)
    events=[e for e in p.activity_events if e.customer_id in ids and e.on<=as_of]
    by_day={d.date():set() for d in pd.date_range(start,as_of)}
    for e in events:
        by_day[e.on].add(e.customer_id)
    def active(first,last):
        return set().union(*(v for d,v in by_day.items() if first<=d<=last))
    current=active(as_of-timedelta(days=29),as_of)
    previous=active(as_of-timedelta(days=59),as_of-timedelta(days=30))
    full30=as_of-timedelta(days=29)>=start
    full60=as_of-timedelta(days=59)>=start
    lost=previous-current
    daily=[]
    for day,users in by_day.items():
        rolling=active(day-timedelta(days=29),day)
        daily.append({"Date":pd.Timestamp(day),"Daily active users":len(users),
                      "30-day active users":len(rolling) if day-timedelta(days=29)>=start else None,
                      "New paid customers":sum(c.id in ids and c.purchased_on==day for c in p.customers)})
    monthly=[]
    for month in pd.period_range(start,as_of,freq="M"):
        first,last=month.start_time.date(),month.end_time.date()
        observed_last=min(last,as_of)
        days=[v for d,v in by_day.items() if first<=d<=observed_last]
        monthly.append({"Month":str(month),"Active users":len(active(first,observed_last)),
                        "Average DAU":round(sum(map(len,days))/len(days),1),
                        "Coverage":"Partial" if first<start or last>as_of else "Complete"})
    return {"daily":pd.DataFrame(daily),"monthly":pd.DataFrame(monthly),"dau":len(by_day[as_of]),
            "previous_dau":len(by_day[as_of-timedelta(days=1)]) if as_of>start else None,
            "mau":len(current) if full30 else None,"previous_mau":len(previous) if full60 else None,
            "growth":(len(current)-len(previous))/len(previous) if full60 and previous else None,
            "churn":len(lost)/len(previous) if full60 and previous else None,
            "retention":len(previous&current)/len(previous) if full60 and previous else None,
            "lost":lost if full60 else set(),"retained":previous&current if full60 else set(),
            "newly_active":current-previous if full60 else set(),"eligible":len(previous) if full60 else None,
            "events_today":[e.model_dump() for e in events if e.on==as_of],"customers":len(ids)}
