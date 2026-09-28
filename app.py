import json
import math
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import BASE_DIR, LLM_PROVIDER, OPENAI_MODEL
from database.db import (
    ensure_seeded_criteria, get_active_criteria, get_all_criteria,
    update_criterion, recent_runs
)
from agents.orchestrator_agent import run_evaluation
from tools.pdf_tool import extract_pdf_text
from tools.validation_tool import validate_and_normalize

# ============================================================
# Application shell
# ============================================================
st.set_page_config(
    page_title="Procurement Decision Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
ensure_seeded_criteria()
BASE = Path(BASE_DIR)

st.markdown("""
<style>
:root{
 --ink:#111827; --muted:#697386; --line:#E6E9F0; --panel:#FFFFFF;
 --nav:#0D1530; --accent:#6957F5; --accent2:#8E79FF; --soft:#F2F0FF;
 --green:#15966A; --greenSoft:#ECFAF4; --amber:#B76E00; --amberSoft:#FFF7E8;
 --red:#C33B4A; --redSoft:#FFF0F2; --blue:#3972D7; --blueSoft:#EEF5FF;
}
.stApp{
 background:
  radial-gradient(circle at 80% -5%, rgba(105,87,245,.14), transparent 28%),
  linear-gradient(180deg,#FBFCFF 0%,#F5F7FB 100%);
}
.block-container{max-width:1600px;padding:1.1rem 2rem 3rem;}
[data-testid="stSidebar"]{
 background:
  radial-gradient(circle at 20% 0%,rgba(105,87,245,.22),transparent 28%),
  linear-gradient(180deg,#0C142C 0%,#111A38 100%);
 border-right:1px solid rgba(255,255,255,.06);
}
[data-testid="stSidebar"] *{color:#F7F8FD;}
[data-testid="stSidebar"] .stRadio label{
 padding:.44rem .48rem;border-radius:10px;margin-bottom:.08rem;
}
[data-testid="stSidebar"] .stRadio label:hover{background:rgba(255,255,255,.06);}
h1,h2,h3{color:var(--ink);letter-spacing:-.028em;}
.topbar{
 display:flex;align-items:center;justify-content:space-between;
 background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:18px;
 padding:16px 20px;margin-bottom:15px;box-shadow:0 10px 28px rgba(15,23,42,.045);
}
.brand-title{font-size:1.38rem;font-weight:850;color:var(--ink);}
.brand-sub{font-size:.78rem;color:var(--muted);margin-top:3px;}
.status-row{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.chip{font-size:.71rem;font-weight:750;padding:6px 10px;border-radius:999px;border:1px solid var(--line);background:#fff;color:#4E566B}
.chip.live{background:var(--greenSoft);color:#14704F;border-color:#CBEEDF}
.chip.sim{background:var(--blueSoft);color:#295DAD;border-color:#D4E4FF}
.hero{
 background:
  radial-gradient(circle at 84% 10%, rgba(132,103,255,.16), transparent 28%),
  linear-gradient(135deg,#FFFFFF 0%,#FAFAFF 100%);
 border:1px solid var(--line);border-radius:24px;padding:28px 30px;
 box-shadow:0 14px 40px rgba(15,23,42,.055);margin-bottom:18px;
}
.eyebrow{font-size:.7rem;letter-spacing:.12em;font-weight:850;color:#6E5CEC;text-transform:uppercase}
.hero h1{font-size:2.25rem;margin:.32rem 0 .42rem}
.hero p{margin:0;color:var(--muted);max-width:900px;font-size:.98rem}
.kpi{
 background:#fff;border:1px solid var(--line);border-radius:17px;padding:16px 17px;
 min-height:108px;box-shadow:0 7px 24px rgba(15,23,42,.035);
}
.kpi-label{font-size:.69rem;letter-spacing:.08em;text-transform:uppercase;color:#8B93A6;font-weight:800}
.kpi-value{font-size:1.48rem;color:var(--ink);font-weight:850;margin-top:7px;line-height:1.05}
.kpi-foot{font-size:.74rem;color:#9298A8;margin-top:7px}
.section{
 background:#fff;border:1px solid var(--line);border-radius:19px;padding:18px 20px;
 box-shadow:0 7px 24px rgba(15,23,42,.035);margin-bottom:14px;
}
.stage{
 background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px;
 min-height:102px;box-shadow:0 5px 18px rgba(15,23,42,.03);
}
.stage-num{
 width:24px;height:24px;border-radius:8px;background:var(--soft);color:var(--accent);
 display:flex;align-items:center;justify-content:center;font-size:.68rem;font-weight:850
}
.stage-title{font-size:.79rem;color:var(--ink);font-weight:850;margin-top:9px}
.stage-sub{font-size:.68rem;color:#8C93A3;margin-top:4px;line-height:1.25}
.risk-high{background:var(--redSoft);color:#A22B39;border:1px solid #FFD6DC;border-radius:999px;padding:4px 8px;font-size:.68rem;font-weight:800}
.risk-med{background:var(--amberSoft);color:#8F5804;border:1px solid #FFE1AD;border-radius:999px;padding:4px 8px;font-size:.68rem;font-weight:800}
.risk-low{background:var(--greenSoft);color:#15714F;border:1px solid #CBEEDF;border-radius:999px;padding:4px 8px;font-size:.68rem;font-weight:800}
.trace{
 padding:9px 11px;border-radius:10px;background:#F7FAFD;border:1px solid #E8ECF2;
 margin-bottom:7px;color:#425067;font-size:.83rem
}
.control{
 padding:13px 15px;border-radius:13px;background:#FAF9FF;border:1px solid #DEDAFF;color:#514A7A
}
.supplier-card{
 background:#fff;border:1px solid var(--line);border-radius:17px;padding:16px 17px;
 box-shadow:0 6px 20px rgba(15,23,42,.035);min-height:142px
}
.rank-badge{
 display:inline-flex;width:30px;height:30px;border-radius:10px;background:#111A38;color:white;
 align-items:center;justify-content:center;font-weight:850;font-size:.78rem
}
.supplier-name{font-size:1.08rem;font-weight:850;color:var(--ink);margin-top:10px}
.supplier-meta{font-size:.73rem;color:#858D9E;margin-top:3px}
.score-big{font-size:1.45rem;font-weight:850;color:#4F46D9}
.small-muted{font-size:.75rem;color:#858D9E}
.footer-note{font-size:.72rem;color:#9AA1AF;text-align:center;margin-top:18px}
</style>
""", unsafe_allow_html=True)

# ============================================================
# UI helpers
# ============================================================
def topbar():
    runtime = "Live LLM" if LLM_PROVIDER != "mock" else "Deterministic Simulation"
    runtime_cls = "live" if LLM_PROVIDER != "mock" else "sim"
    run = st.session_state.get("run_id","No active run")
    st.markdown(
        f"""<div class="topbar">
          <div><div class="brand-title">◈ Procurement Decision Intelligence</div>
          <div class="brand-sub">Evidence-grounded supplier evaluation · deterministic procurement controls</div></div>
          <div class="status-row">
            <span class="chip {runtime_cls}">{runtime}</span>
            <span class="chip">SQLite · Operational</span>
            <span class="chip">{run}</span>
          </div>
        </div>""", unsafe_allow_html=True
    )

def hero(title, subtitle, eyebrow):
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True
    )

def kpi(label, value, foot=""):
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-foot">{foot}</div></div>',
        unsafe_allow_html=True
    )

def stage_pipeline():
    stages=[
        ("01","Policy","criteria + weights"),
        ("02","Ingest","requirement + proposals"),
        ("03","Extract","document evidence"),
        ("04","Evaluate","LLM criterion judgment"),
        ("05","Validate","schema + ranges"),
        ("06","Score","weighted arithmetic"),
        ("07","Benchmark","PPI + gaps"),
        ("08","Decide","stable ranking"),
        ("09","Persist","audit record"),
    ]
    cols=st.columns(9)
    for c,(n,t,s) in zip(cols,stages):
        with c:
            st.markdown(
                f'<div class="stage"><div class="stage-num">{n}</div><div class="stage-title">{t}</div>'
                f'<div class="stage-sub">{s}</div></div>',unsafe_allow_html=True
            )

def reference_suppliers():
    return [
        {"supplier_name":"Apex Systems","submission_date":"2026-08-26","experience_rating":8.8,
         "industry":"Enterprise Software","area":"Hyderabad",
         "pdf":str(BASE/"sample_rfps"/"Apex_Systems.pdf"),"pdf_name":"Apex_Systems.pdf"},
        {"supplier_name":"BrightPath Tech","submission_date":"2026-08-24","experience_rating":6.4,
         "industry":"IT Services","area":"Bengaluru",
         "pdf":str(BASE/"sample_rfps"/"BrightPath_Tech.pdf"),"pdf_name":"BrightPath_Tech.pdf"},
        {"supplier_name":"NexaWorks","submission_date":"2026-08-25","experience_rating":8.2,
         "industry":"Enterprise Software","area":"Hyderabad",
         "pdf":str(BASE/"sample_rfps"/"NexaWorks.pdf"),"pdf_name":"NexaWorks.pdf"},
        {"supplier_name":"Orbit Digital","submission_date":"2026-08-23","experience_rating":9.1,
         "industry":"IT Services","area":"Bengaluru",
         "pdf":str(BASE/"sample_rfps"/"Orbit_Digital.pdf"),"pdf_name":"Orbit_Digital.pdf"},
    ]

def execute_run(requirement, suppliers):
    with st.status("Orchestrating evaluation run", expanded=True) as s:
        messages=[
            "Policy loaded from SQLite",
            "Buyer requirement evidence extracted",
            f"{len(suppliers)} supplier proposals normalized",
            f"Evidence evaluation dispatched via {LLM_PROVIDER.upper()} runtime",
            "Criterion payloads passed validation controls",
            "Weighted score computation completed",
            "Overall / area / industry peer benchmarks computed",
            "Deterministic ranking rule applied",
            "Run and result payload persisted",
        ]
        for i,m in enumerate(messages):
            st.write(f"{i+1:02d} · {m}")
            if i==2:
                run_id, rs = run_evaluation(requirement, suppliers)
        s.update(label="Evaluation run completed",state="complete",expanded=False)
    st.session_state.run_id=run_id
    st.session_state.results=rs
    st.session_state.last_suppliers=suppliers
    st.session_state.last_requirement=requirement

def risk_level(r):
    risks=len(r.get("risks",[]))
    warnings=len(r.get("warnings",[]))
    security=next((c["score"]/c["max_score"] for c in r["criteria"] if "Security" in c["criterion_name"]),1)
    if warnings>=2 or security<.6 or risks>=3: return "High"
    if warnings or security<.8 or risks>=1: return "Medium"
    return "Low"

def board_df(results):
    return pd.DataFrame([{
        "Rank":r["final_rank"],"Supplier":r["supplier_name"],
        "Absolute Score":round(r["absolute_score"],2),"Overall PPI":round(r["ppi"],2),
        "Area PPI":round(r.get("area_ppi",0),2),"Industry PPI":round(r.get("industry_ppi",0),2),
        "Experience":round(r["experience_rating"],1),"Area":r.get("area",""),
        "Industry":r.get("industry",""),"Risk":risk_level(r),
        "Submission":r["submission_date"]
    } for r in results]).sort_values("Rank")

def radar_chart(r):
    names=[c["criterion_name"] for c in r["criteria"]]
    vals=[c["score"]/c["max_score"]*100 for c in r["criteria"]]
    vals += vals[:1]; names += names[:1]
    fig=go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals,theta=names,fill="toself",name=r["supplier_name"]))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True,range=[0,100])),
        showlegend=False,height=380,margin=dict(l=35,r=35,t=30,b=30),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def criterion_heatmap(results):
    rows=[]
    for r in results:
        for c in r["criteria"]:
            rows.append({"Supplier":r["supplier_name"],"Criterion":c["criterion_name"],
                         "Score %":round(c["score"]/c["max_score"]*100,1)})
    df=pd.DataFrame(rows)
    pivot=df.pivot(index="Supplier",columns="Criterion",values="Score %")
    fig=px.imshow(pivot,text_auto=".0f",aspect="auto",zmin=0,zmax=100,
                  color_continuous_scale="RdYlGn")
    fig.update_layout(height=360,margin=dict(l=20,r=20,t=30,b=20),coloraxis_colorbar_title="Score %")
    return fig

def deterministic_summary(r):
    strongest=max(r["criteria"],key=lambda c:c["relative_percentage"])
    weakest=min(r["criteria"],key=lambda c:c["relative_percentage"])
    return (f'Rank #{r["final_rank"]} with {r["absolute_score"]:.1f}/100 absolute score and '
            f'{r["ppi"]:.1f}% PPI. Strongest relative area: {strongest["criterion_name"]}; '
            f'largest peer gap: {weakest["criterion_name"]} ({weakest["gap"]:.1f}).')

def what_if_scores(results, weights):
    out=[]
    for r in results:
        absolute=0
        relative=0
        for c in r["criteria"]:
            w=weights.get(c["criterion_id"],0)
            absolute += (c["score"]/c["max_score"])*w
            relative += c["relative_percentage"]*w
        total=sum(weights.values()) or 1
        out.append({
            "Supplier":r["supplier_name"],
            "Scenario Score":absolute,
            "Scenario PPI":relative/total,
            "Submission":r["submission_date"],
            "Experience":r["experience_rating"],
        })
    out.sort(key=lambda x:(-x["Scenario PPI"],x["Submission"],-x["Experience"],x["Supplier"].lower()))
    for i,x in enumerate(out,1): x["Scenario Rank"]=i
    return pd.DataFrame(out)[["Scenario Rank","Supplier","Scenario Score","Scenario PPI"]]

# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown("## ◈ PDI Control Plane")
    st.caption("Procurement Decision Intelligence")
    st.divider()
    nav=st.radio("Navigation",[
        "Command Center",
        "RFP Intake",
        "Decision Board",
        "All Supplier Evaluations",
        "Supplier 360",
        "Benchmark Matrix",
        "Scenario Lab",
        "Criteria Governance",
        "Risk & Controls",
        "Audit Explorer",
        "Architecture",
    ],label_visibility="collapsed")
    st.divider()
    st.caption("RUNTIME")
    if LLM_PROVIDER=="mock":
        st.info("Deterministic Simulation")
    else:
        st.success(f"Live · {OPENAI_MODEL}")
    st.caption("Decision math remains deterministic in both modes.")

criteria=get_active_criteria()
weight_total=sum(float(c["weight"]) for c in criteria)
results=st.session_state.get("results",[])
topbar()

# ============================================================
# Pages
# ============================================================
if nav=="Command Center":
    hero("Procurement Decision Command Center",
         "A governed control plane for supplier evidence, scoring policy, peer intelligence, risk signals and auditable award decisions.",
         "EXECUTIVE OPERATIONS")
    stage_pipeline()
    st.write("")

    cols=st.columns(6)
    winner=min(results,key=lambda r:r["final_rank"]) if results else None
    run_risk=sum(1 for r in results if risk_level(r)=="High") if results else 0
    values=[
        ("Evaluation State","READY" if not results else "DECISION READY","run control status"),
        ("Suppliers",len(results),"active evaluation"),
        ("Criteria",len(criteria),f"{weight_total:.0f}% policy weight"),
        ("Leader",winner["supplier_name"] if winner else "—","current deterministic rank #1"),
        ("Highest PPI",f'{max([r["ppi"] for r in results],default=0):.1f}%',"peer performance"),
        ("High Risk",run_risk,"suppliers requiring review"),
    ]
    for c,v in zip(cols,values):
        with c:kpi(*v)

    st.write("")
    if not results:
        a,b=st.columns([1.45,1])
        with a:
            st.markdown('<div class="section">',unsafe_allow_html=True)
            st.subheader("Decision platform overview")
            st.write("Create an RFP run from supplier PDFs or validate the platform using the packaged reference portfolio.")
            st.markdown("**Control boundary**")
            st.markdown('<div class="control"><b>AI interprets evidence.</b> Python owns score arithmetic, peer benchmarks, PPI, tie-breaks and final rank.</div>',unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)
        with b:
            st.markdown("### Reference portfolio")
            st.caption("Synthetic procurement data packaged with the repository for functional validation.")
            if st.button("Evaluate Reference Portfolio",type="primary",use_container_width=True):
                execute_run(str(BASE/"requirements"/"Procurement_Requirement.pdf"),reference_suppliers())
                st.rerun()
    else:
        board=board_df(results)
        c1,c2=st.columns([1.2,1])
        with c1:
            st.subheader("Decision leaderboard")
            st.dataframe(board[["Rank","Supplier","Absolute Score","Overall PPI","Risk"]],
                         use_container_width=True,hide_index=True)
        with c2:
            fig=px.scatter(board,x="Absolute Score",y="Overall PPI",size="Experience",
                           text="Supplier",hover_data=["Risk","Area","Industry"],title="Quality vs peer performance")
            fig.update_traces(textposition="top center")
            fig.update_layout(height=350,margin=dict(l=20,r=20,t=45,b=20))
            st.plotly_chart(fig,use_container_width=True)
        st.subheader("Criterion performance heatmap")
        st.plotly_chart(criterion_heatmap(results),use_container_width=True)

elif nav=="RFP Intake":
    hero("RFP Intake & Orchestration",
         "Create a governed evaluation batch from a buyer requirement document and either one supplier proposal or a portfolio of supplier proposals.",
         "BATCH CREATION")

    a,b,c,d=st.columns(4)
    with a:kpi("Policy Check","PASS" if abs(weight_total-100)<1e-6 else "BLOCKED",f"active weight {weight_total:.0f}%")
    with b:kpi("Evidence Format","PDF","text-layer extraction")
    with c:kpi("Supplier Modes","1 / MANY","single or portfolio")
    with d:kpi("Ranking Rule","LOCKED","PPI -> date -> experience -> name")

    intake_mode = st.radio(
        "Evaluation mode",
        options=["Single Supplier", "Multiple Suppliers"],
        horizontal=True
    )

    requirement=st.file_uploader(
        "Buyer requirement / RFP PDF",
        type=["pdf"],
        key=f"requirement_{intake_mode}"
    )

    supplier_inputs=[]

    if intake_mode=="Single Supplier":
        st.subheader("Supplier proposal")
        pdf=st.file_uploader(
            "Supplier proposal PDF",
            type=["pdf"],
            accept_multiple_files=False,
            key="single_supplier_pdf"
        )
        if pdf is not None:
            with st.container(border=True):
                c1,c2,c3=st.columns(3)
                name=c1.text_input(
                    "Supplier",
                    pdf.name.rsplit(".",1)[0].replace("_"," ").title(),
                    key="single_name"
                )
                submitted=c2.date_input("Submission date",date.today(),key="single_date")
                exp=c3.slider("Historical experience",0.0,10.0,7.0,.1,key="single_exp")
                c4,c5=st.columns(2)
                industry=c4.text_input("Industry segment","IT Services",key="single_industry")
                area=c5.text_input("Operating area","India",key="single_area")
                supplier_inputs.append({
                    "supplier_name":name,
                    "submission_date":submitted.isoformat(),
                    "experience_rating":exp,
                    "industry":industry,
                    "area":area,
                    "pdf":pdf,
                    "pdf_name":pdf.name
                })

        st.caption("Single-supplier mode evaluates one proposal. Comparative PPI becomes more meaningful when additional suppliers are evaluated together.")

    else:
        st.subheader("Supplier portfolio")
        proposals=st.file_uploader(
            "Supplier proposal PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key="multi_supplier_pdfs",
            help="Upload two or more supplier proposals for concurrent evaluation and peer benchmarking."
        )

        if proposals:
            st.caption(f"{len(proposals)} supplier proposal(s) selected")

        for i,pdf in enumerate(proposals or []):
            with st.expander(f"{i+1:02d} - {pdf.name}",expanded=True):
                c1,c2,c3=st.columns(3)
                name=c1.text_input(
                    "Supplier",
                    pdf.name.rsplit(".",1)[0].replace("_"," ").title(),
                    key=f"sn{i}"
                )
                submitted=c2.date_input("Submission date",date.today(),key=f"sd{i}")
                exp=c3.slider("Historical experience",0.0,10.0,7.0,.1,key=f"se{i}")
                c4,c5=st.columns(2)
                industry=c4.text_input("Industry segment","IT Services",key=f"si{i}")
                area=c5.text_input("Operating area","India",key=f"sa{i}")
                supplier_inputs.append({
                    "supplier_name":name,
                    "submission_date":submitted.isoformat(),
                    "experience_rating":exp,
                    "industry":industry,
                    "area":area,
                    "pdf":pdf,
                    "pdf_name":pdf.name
                })

    launch_label = "Evaluate Supplier" if intake_mode=="Single Supplier" else "Evaluate Supplier Portfolio"
    if st.button(
        launch_label,
        type="primary",
        use_container_width=True,
        disabled=not supplier_inputs
    ):
        if requirement is None:
            st.error("Buyer requirement PDF is required.")
        elif abs(weight_total-100)>1e-6:
            st.error("Policy weights must total 100%.")
        else:
            execute_run(requirement,supplier_inputs)
            st.success(f"Evaluation completed for {len(supplier_inputs)} supplier(s) and persisted.")

    with st.expander("Reference data utilities"):
        st.caption("Execute the packaged synthetic supplier portfolio to validate end-to-end deployment behavior.")
        if st.button("Evaluate Packaged Portfolio",use_container_width=True):
            execute_run(str(BASE/"requirements"/"Procurement_Requirement.pdf"),reference_suppliers())
            st.rerun()

elif nav=="Decision Board":
    hero("Decision Board",
         "Executive ranking, award rationale, criterion evidence and deterministic decision trace in one workspace.",
         "AWARD DECISION")
    if not results:
        st.warning("No active evaluation. Create a run from RFP Intake.")
    else:
        board=board_df(results)
        winner=min(results,key=lambda r:r["final_rank"])
        cols=st.columns(5)
        metrics=[
            ("Recommended Supplier",winner["supplier_name"],"deterministic rank #1"),
            ("Absolute Score",f'{winner["absolute_score"]:.1f}/100',"weighted score"),
            ("Peer Index",f'{winner["ppi"]:.1f}%',"overall PPI"),
            ("Risk",risk_level(winner),"control signal"),
            ("Experience",f'{winner["experience_rating"]:.1f}/10',"historical rating"),
        ]
        for c,v in zip(cols,metrics):
            with c:kpi(*v)
        st.markdown(f'<div class="control"><b>Decision rationale:</b> {deterministic_summary(winner)}</div>',unsafe_allow_html=True)
        st.write("")
        st.dataframe(board,use_container_width=True,hide_index=True)
        c1,c2=st.columns([1,1])
        with c1:
            st.plotly_chart(criterion_heatmap(results),use_container_width=True)
        with c2:
            fig=px.bar(board,x="Supplier",y=["Overall PPI","Area PPI","Industry PPI"],barmode="group")
            fig.update_layout(height=360,margin=dict(l=20,r=20,t=30,b=20),legend_title="")
            st.plotly_chart(fig,use_container_width=True)

elif nav=="All Supplier Evaluations":
    hero("All Supplier Evaluations",
         "Review every supplier in the active RFP run concurrently, including final rank, weighted score, peer indices, criterion scores, evidence, justification, risks and validation warnings.",
         "CONCURRENT SUPPLIER REVIEW")

    if not results:
        st.warning("No active evaluation. Create a run from RFP Intake.")
    else:
        ordered=sorted(results,key=lambda r:r["final_rank"])
        board=board_df(ordered)

        c1,c2,c3,c4,c5=st.columns(5)
        with c1:kpi("Suppliers",len(ordered),"active evaluation run")
        with c2:kpi("Top Ranked",ordered[0]["supplier_name"],"deterministic rank #1")
        with c3:kpi("Best Absolute",f'{max(r["absolute_score"] for r in ordered):.1f}',"weighted score")
        with c4:kpi("Best PPI",f'{max(r["ppi"] for r in ordered):.1f}%',"overall peer index")
        with c5:kpi("Risk Review",sum(1 for r in ordered if risk_level(r)!="Low"),"medium / high risk")

        st.subheader("Portfolio leaderboard")
        st.dataframe(
            board[["Rank","Supplier","Absolute Score","Overall PPI","Area PPI","Industry PPI","Experience","Risk","Submission"]],
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Concurrent supplier summary")
        for start_idx in range(0,len(ordered),3):
            cols=st.columns(3)
            for col,r in zip(cols,ordered[start_idx:start_idx+3]):
                with col:
                    risk=risk_level(r)
                    risk_cls={"High":"risk-high","Medium":"risk-med","Low":"risk-low"}[risk]
                    card = (
                        '<div class="supplier-card">'
                        f'<div class="rank-badge">#{r["final_rank"]}</div>'
                        f'<div class="supplier-name">{r["supplier_name"]}</div>'
                        f'<div class="supplier-meta">{r.get("area","")} | {r.get("industry","")}</div>'
                        '<div style="display:flex;justify-content:space-between;align-items:end;margin-top:13px">'
                        f'<div><div class="small-muted">Absolute Score</div><div class="score-big">{r["absolute_score"]:.1f}</div></div>'
                        f'<div><div class="small-muted">Overall PPI</div><div class="score-big">{r["ppi"]:.1f}%</div></div>'
                        '</div>'
                        f'<div style="margin-top:10px"><span class="{risk_cls}">{risk} Risk</span></div>'
                        '</div>'
                    )
                    st.markdown(card, unsafe_allow_html=True)

        st.subheader("Cross-supplier criterion matrix")
        st.plotly_chart(criterion_heatmap(ordered),use_container_width=True)

        criterion_rows=[]
        for r in ordered:
            for c in r["criteria"]:
                criterion_rows.append({
                    "Rank":r["final_rank"],
                    "Supplier":r["supplier_name"],
                    "Criterion":c["criterion_name"],
                    "Score":c["score"],
                    "Max":c["max_score"],
                    "Weight %":c["weight"],
                    "Weighted Contribution":round(c["weighted_score"],2),
                    "Peer Benchmark":c["benchmark_score"],
                    "Gap":c["gap"],
                    "Relative %":round(c["relative_percentage"],2)
                })
        criterion_df=pd.DataFrame(criterion_rows)
        st.dataframe(criterion_df,use_container_width=True,hide_index=True)

        st.subheader("Complete evaluation details")
        st.caption("All supplier evaluations remain on this page. Expand or collapse any supplier independently.")

        for r in ordered:
            risk=risk_level(r)
            title=(
                f'#{r["final_rank"]} - {r["supplier_name"]} - '
                f'Absolute {r["absolute_score"]:.1f} - PPI {r["ppi"]:.1f}% - {risk} Risk'
            )
            with st.expander(title,expanded=True):
                a,b,c,d,e,f=st.columns(6)
                metrics=[
                    ("Rank",f'#{r["final_rank"]}',"final order"),
                    ("Absolute",f'{r["absolute_score"]:.1f}',"weighted score"),
                    ("PPI",f'{r["ppi"]:.1f}%',"overall peers"),
                    ("Area PPI",f'{r.get("area_ppi",0):.1f}%',r.get("area","")),
                    ("Industry PPI",f'{r.get("industry_ppi",0):.1f}%',r.get("industry","")),
                    ("Experience",f'{r["experience_rating"]:.1f}/10',"historical")
                ]
                for col,m in zip([a,b,c,d,e,f],metrics):
                    with col:kpi(*m)

                st.markdown(f"**Decision summary:** {deterministic_summary(r)}")
                if r.get("overall_summary"):
                    st.markdown(f"**Evaluation summary:** {r['overall_summary']}")

                supplier_scorecard=pd.DataFrame([{
                    "Criterion":x["criterion_name"],
                    "Score":x["score"],
                    "Max":x["max_score"],
                    "Weight %":x["weight"],
                    "Weighted Contribution":round(x["weighted_score"],2),
                    "Peer Benchmark":x["benchmark_score"],
                    "Gap":x["gap"],
                    "Relative %":round(x["relative_percentage"],2),
                    "Evidence":x["evidence"],
                    "Justification":x["justification"]
                } for x in r["criteria"]])

                st.dataframe(supplier_scorecard,use_container_width=True,hide_index=True)

                left,right=st.columns([1,1])
                with left:
                    st.plotly_chart(
                        radar_chart(r),
                        use_container_width=True,
                        key=f'radar_all_{r["final_rank"]}_{r["supplier_name"]}'
                    )
                with right:
                    chart_df=supplier_scorecard.set_index("Criterion")[["Score","Peer Benchmark"]]
                    st.bar_chart(chart_df)

                st.markdown("##### Criterion evidence and reasoning")
                for x in r["criteria"]:
                    st.markdown(
                        f'**{x["criterion_name"]} - {x["score"]}/{x["max_score"]} '
                        f'| weight {x["weight"]}% | peer gap {x["gap"]:.1f}**'
                    )
                    ev1,ev2=st.columns(2)
                    with ev1:
                        st.markdown("**Evidence**")
                        st.write(x["evidence"])
                    with ev2:
                        st.markdown("**Justification**")
                        st.write(x["justification"])
                    st.divider()

                if r.get("risks"):
                    st.markdown("##### Observed risks")
                    for item in r["risks"]:
                        st.warning(item)
                if r.get("warnings"):
                    st.markdown("##### Validation warnings")
                    for item in r["warnings"]:
                        st.info(item)

        decision_package={
            "rfp_run_id":st.session_state.get("run_id"),
            "supplier_count":len(ordered),
            "ranking_rule":"PPI DESC -> submission date ASC -> experience DESC -> supplier name ASC",
            "results":ordered
        }
        st.download_button(
            "Export Complete Supplier Evaluation Package (JSON)",
            json.dumps(decision_package,indent=2),
            file_name=f'{st.session_state.get("run_id","rfp_run")}_all_suppliers.json',
            mime="application/json",
            use_container_width=True
        )

elif nav=="Supplier 360":
    hero("Supplier 360",
         "Evidence, criterion performance, peer gaps, risk indicators and supplier context in a single analytical profile.",
         "SUPPLIER INTELLIGENCE")
    if not results:
        st.warning("No active evaluation.")
    else:
        names=[r["supplier_name"] for r in sorted(results,key=lambda r:r["final_rank"])]
        sel=st.selectbox("Supplier",names)
        r=next(x for x in results if x["supplier_name"]==sel)
        a,b,c,d,e=st.columns(5)
        for col,v in zip([a,b,c,d,e],[
            ("Rank",f'#{r["final_rank"]}',"decision order"),
            ("Absolute",f'{r["absolute_score"]:.1f}',"weighted score"),
            ("PPI",f'{r["ppi"]:.1f}%',"overall peers"),
            ("Area PPI",f'{r.get("area_ppi",0):.1f}% ',r.get("area","")),
            ("Risk",risk_level(r),f'{len(r.get("risks",[]))} observed risk(s)'),
        ]):
            with col:kpi(*v)

        c1,c2=st.columns([1,1.25])
        with c1:
            st.plotly_chart(radar_chart(r),use_container_width=True)
        with c2:
            scorecard=pd.DataFrame([{
                "Criterion":x["criterion_name"],"Score":x["score"],"Max":x["max_score"],
                "Weight":x["weight"],"Benchmark":x["benchmark_score"],"Gap":x["gap"],
                "Relative %":x["relative_percentage"]
            } for x in r["criteria"]])
            st.subheader("Criterion scorecard")
            st.dataframe(scorecard,use_container_width=True,hide_index=True)

        st.subheader("Evidence & reasoning")
        for x in r["criteria"]:
            with st.expander(f'{x["criterion_name"]} · {x["score"]}/{x["max_score"]} · peer gap {x["gap"]}'):
                st.markdown(f"**Evidence:** {x['evidence']}")
                st.markdown(f"**Justification:** {x['justification']}")
                st.caption(f"Weight {x['weight']}% · benchmark {x['benchmark_score']} · relative {x['relative_percentage']:.1f}%")
        if r.get("risks"):
            st.subheader("Observed risks")
            for item in r["risks"]: st.markdown(f"- {item}")

elif nav=="Benchmark Matrix":
    hero("Benchmark Matrix",
         "Cross-supplier criterion benchmarking with overall, regional and industry-relative performance views.",
         "PEER ANALYTICS")
    if not results:
        st.warning("No active evaluation.")
    else:
        board=board_df(results)
        st.plotly_chart(criterion_heatmap(results),use_container_width=True)
        c1,c2=st.columns(2)
        with c1:
            fig=px.scatter(board,x="Overall PPI",y="Area PPI",size="Absolute Score",
                           color="Risk",text="Supplier",title="Overall vs area peers")
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            fig=px.scatter(board,x="Overall PPI",y="Industry PPI",size="Absolute Score",
                           color="Risk",text="Supplier",title="Overall vs industry peers")
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig,use_container_width=True)
        st.dataframe(board[["Supplier","Overall PPI","Area PPI","Industry PPI","Area","Industry","Risk"]],
                     use_container_width=True,hide_index=True)

elif nav=="Scenario Lab":
    hero("Scenario Lab",
         "Explore non-persistent policy scenarios without changing the governed production criteria or the persisted evaluation run.",
         "WHAT-IF ANALYSIS")
    if not results:
        st.warning("No active evaluation.")
    else:
        st.info("Scenario calculations are analytical only. They do not modify SQLite policy or the persisted final rank.")
        st.subheader("Scenario weights")
        weights={}
        cols=st.columns(len(criteria))
        for col,c in zip(cols,criteria):
            with col:
                weights[c["criterion_id"]]=st.number_input(
                    c["name"],min_value=0.0,max_value=100.0,value=float(c["weight"]),step=5.0,key=f'w{c["criterion_id"]}'
                )
        scenario_total=sum(weights.values())
        if abs(scenario_total-100)<1e-6:
            st.success("Scenario weights = 100%")
            scenario=what_if_scores(results,weights)
            st.dataframe(scenario,use_container_width=True,hide_index=True)
            fig=px.bar(scenario,x="Supplier",y=["Scenario Score","Scenario PPI"],barmode="group")
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.error(f"Scenario weights currently total {scenario_total:.0f}%. Set them to 100%.")

elif nav=="Criteria Governance":
    hero("Criteria Governance",
         "Manage evaluation policy as data. Changes are stored in SQLite and enforced before new evaluation runs.",
         "POLICY MANAGEMENT")
    allc=get_all_criteria()
    st.dataframe(pd.DataFrame(allc),use_container_width=True,hide_index=True)
    active=get_active_criteria()
    fig=px.pie(pd.DataFrame(active),names="name",values="weight",hole=.62,title="Active policy weight distribution")
    fig.update_layout(height=350)
    st.plotly_chart(fig,use_container_width=True)

    chosen=st.selectbox("Policy criterion",allc,format_func=lambda x:f'{x["criterion_id"]} · {x["name"]}')
    a,b,c=st.columns(3)
    weight=a.number_input("Weight %",0.0,100.0,float(chosen["weight"]),1.0)
    maxs=b.number_input("Maximum score",1.0,100.0,float(chosen["max_score"]),1.0)
    active_flag=c.toggle("Active",value=bool(chosen["is_active"]))
    if st.button("Save Policy",type="primary"):
        update_criterion(chosen["criterion_id"],weight,maxs,active_flag)
        st.success("Policy updated.")
        st.rerun()
    if abs(weight_total-100)<1e-6: st.success(f"Governance gate PASS · active weights = {weight_total:.0f}%")
    else: st.error(f"Governance gate BLOCKED · active weights = {weight_total:.0f}%")

elif nav=="Risk & Controls":
    hero("Risk & Controls",
         "Validation gates, model-output normalization and supplier risk signals before deterministic decision logic executes.",
         "CONTROL ASSURANCE")
    invalid={
      "supplier_name":"Control Test Supplier",
      "criteria":[
        {"criterion_id":1,"score":13,"justification":"Out of range","evidence":"Synthetic input"},
        {"criterion_id":2,"score":"invalid","justification":"Non numeric","evidence":""},
        {"criterion_id":4,"score":8,"justification":"Valid","evidence":"Security controls"},
        {"criterion_id":5,"score":7,"justification":"Valid","evidence":"Support SLA"},
      ],
      "risks":["Synthetic validation input"],"overall_summary":"Control payload"
    }
    norm=validate_and_normalize(invalid,"Control Test Supplier",criteria)
    c1,c2=st.columns(2)
    with c1:
        st.subheader("Untrusted evaluation payload");st.json(invalid)
    with c2:
        st.subheader("Normalized control output");st.json(norm)
    st.markdown('<div class="control"><b>Control invariant:</b> malformed, missing or out-of-range model output cannot bypass validation and directly influence scoring.</div>',unsafe_allow_html=True)
    if results:
        st.subheader("Supplier risk register")
        riskdf=pd.DataFrame([{"Supplier":r["supplier_name"],"Risk Level":risk_level(r),
                             "Warnings":len(r.get("warnings",[])),"Observed Risks":len(r.get("risks",[]))}
                            for r in results])
        st.dataframe(riskdf,use_container_width=True,hide_index=True)

elif nav=="Audit Explorer":
    hero("Audit Explorer",
         "Operational run history, execution trace, deterministic rule visibility and exportable decision payloads.",
         "AUDIT & OPERABILITY")
    runs=recent_runs(50)
    if runs: st.dataframe(pd.DataFrame(runs),use_container_width=True,hide_index=True)
    else: st.info("No persisted runs.")
    if results and st.session_state.get("run_id"):
        st.subheader("Current run trace")
        trace=[
            "Policy resolved from SQLite",
            "Buyer requirement extracted",
            f"{len(results)} supplier proposals evaluated",
            "Criterion output validation completed",
            "Weighted scoring executed",
            "Overall / area / industry benchmarking executed",
            "Stable deterministic ranking applied",
            "Supplier and criterion results persisted",
        ]
        for i,t in enumerate(trace,1):
            st.markdown(f'<div class="trace">{i:02d} · {t}</div>',unsafe_allow_html=True)
        payload={"rfp_run_id":st.session_state.run_id,"results":results}
        st.download_button("Export Decision Package (JSON)",json.dumps(payload,indent=2),
                           file_name=f'{st.session_state.run_id}.json',mime="application/json",
                           use_container_width=True)
        st.code("PPI DESC → submission_date ASC → experience DESC → supplier_name ASC")

elif nav=="Architecture":
    hero("Architecture & Decision Boundaries",
         "Modular orchestration that isolates probabilistic document reasoning from deterministic procurement policy and decision controls.",
         "SYSTEM DESIGN")
    st.code("""
┌──────────────────────────────┐
│ Streamlit Decision Console   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Orchestrator Agent           │
│ run lifecycle + sequencing   │
└──────┬───────────┬───────────┘
       │           │
       ▼           ▼
 PDF Tools     SQLite Policy
       │           │
       └─────┬─────┘
             ▼
┌──────────────────────────────┐
│ Evaluation Agent             │
│ evidence → JSON judgment     │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Validation Tool              │
│ schema · completeness · range│
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Deterministic Decision Layer │
│ scoring · benchmark · PPI    │
│ stable ranking               │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ SQLite Audit Persistence     │
└──────────────┬───────────────┘
               ▼
  dashboards · scorecards · export
""",language="text")
    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown("### Probabilistic boundary")
        st.write("Document interpretation, evidence selection, qualitative criterion judgment.")
    with c2:
        st.markdown("### Deterministic boundary")
        st.write("Validation, arithmetic, benchmarks, PPI, tie-breaks, final rank.")
    with c3:
        st.markdown("### Audit boundary")
        st.write("Criteria policy, run identity, supplier results, criterion results, exported JSON.")

st.markdown('<div class="footer-note">Procurement Decision Intelligence · governed supplier evaluation platform<br>Copyright © 2026 Kavali Naresh Kumar. All rights reserved.</div>',unsafe_allow_html=True)
