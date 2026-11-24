# =============================================================================
# PHASE 3 - INTERACTIVE DASHBOARD (Streamlit)
# -----------------------------------------------------------------------------
# Plain English: a web page where anyone can change the yard (tippler speed,
# loading speed, placement time, locos...) and the digital twin re-plays
# July 2025 to show how demurrage changes.
# Run on your computer with:   streamlit run app.py
# =============================================================================

from dataclasses import replace                       # "Copy a scenario and change some settings"
import altair as alt                                  # "Charts that work inside Streamlit"
import pandas as pd                                   # "Tables"
import streamlit as st                                # "The web-page toolbox"
from rake_twin_sim import Scenario, load_data, run_many   # "Our virtual yard from Phase 2"

GREY, BLUE, INK = "#8a8985", "#2a78d6", "#0b0b0b"     # "Chart colours: grey = July, blue = your scenario"

st.set_page_config(page_title="Rake Turnaround Digital Twin", page_icon="🚆", layout="wide")  # "Page title and wide layout"

# ---------------------------------------------------------------------------
# Data and baseline (computed once, then remembered)
# ---------------------------------------------------------------------------
@st.cache_resource                                    # "Do this once and keep it in memory"
def get_data():
    return load_data()                                # "Read July data and the pools of real times"

@st.cache_data(show_spinner=False)                    # "Remember results for the same settings"
def simulate(settings: dict, runs: int):
    inw, out, pools = get_data()                      # "Get the July data"
    sc = replace(Scenario(), **settings)              # "Build a scenario from the chosen settings"
    return run_many(inw, out, pools, sc, runs=runs)   # "Play July 'runs' times"

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🚆 Rake Turnaround Digital Twin")          # "Big page title"
st.caption("A bulk port rail siding (anonymised) · July 2025 · 251 inward + 365 outward rakes · "
           "built by Satish Majji")                  # "One-line description"
st.write("Change the yard on the left and press **Run the twin**. The model re-plays every rake "
         "of July 2025 many times and shows how much demurrage your changes would save.")

# ---------------------------------------------------------------------------
# Sidebar - the controls
# ---------------------------------------------------------------------------
with st.sidebar.form("controls"):                    # "Group the controls; nothing runs until the button"
    st.header("Change the yard")
    tippler = st.slider("Tippler speed (% of July)", 100, 200, 100, 5,
                        help="July: about 10 wagons/hour of actual tipping. Rated: 24 tips/hour.")   # "Tippler speed"
    loading = st.slider("Loading speed (% of July)", 100, 150, 100, 5,
                        help="Silo, wagon loader and manual loading together.")                       # "Loading speed"
    prep_cut = st.slider("Pre-placement time saved (minutes)", 0, 90, 0, 15,
                         help="Examination, weighment and line clearing before a rake is placed.")    # "Placement saving"
    smooth = st.checkbox("Spread each day's inward rakes evenly", value=False)                        # "Even arrivals"
    with st.expander("Resources"):                   # "Less-used controls, folded away"
        locos = st.slider("Locos available", 3, 10, 9)                                                # "Loco fleet"
        manual_lines = st.slider("Manual unloading lines", 3, 8, 5)                                   # "Manual lines"
        silo = st.slider("Silo loading lines", 1, 4, 2)                                               # "Silo lines"
        wl = st.slider("Wagon-loader lines", 1, 4, 2)                                                 # "Wagon loader lines"
    runs = st.select_slider("Runs (more = steadier, slower)", [20, 50, 100], value=50)               # "How many replays"
    go = st.form_submit_button("Run the twin", type="primary", width="stretch")             # "The button"

settings = dict(                                      # "Turn the controls into model settings"
    tippler_speed_factor=tippler / 100, loading_speed_factor=loading / 100,
    placement_cut_h=prep_cut / 60, smooth_inward_arrivals=smooth,
    locos=locos, manual_unload_lines=manual_lines, silo_lines=silo, wagon_loader_lines=wl,
)

with st.spinner("Re-playing July in the virtual yard..."):                     # "Show 'working...' while it runs"
    base = simulate({}, runs)                                                   # "July as it was"
    scen = simulate(settings, runs)                                             # "July with your changes"

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Your scenario", "July 2025 baseline", "How the twin works"])

with tab1:
    b, s = base.mean(), scen.mean()                                             # "Average of all runs"
    saving = b.total_dem_lakh - s.total_dem_lakh                                # "Monthly saving in Rs lakh"
    same = settings == dict(tippler_speed_factor=1.0, loading_speed_factor=1.0, placement_cut_h=0.0,
                            smooth_inward_arrivals=False, locos=9, manual_unload_lines=5,
                            silo_lines=2, wagon_loader_lines=2)                 # "Nothing changed yet?"
    d = (lambda txt: None) if same else (lambda txt: txt)                       # "Then hide the arrows (they would be noise)"
    if same:
        st.info("This is July 2025 as it happened. Move a slider on the left and press **Run the twin**.")
    c1, c2, c3, c4, c5 = st.columns(5)                                          # "Five number tiles in a row"
    c1.metric("Demurrage / month", f"₹{s.total_dem_lakh:.1f} lakh",
              d(f"{-saving:+.1f} lakh vs July"), delta_color="inverse")            # "Lower is better -> inverse colours"
    c2.metric("Saving / year", "—" if same else f"₹{saving * 12 / 100:.2f} crore")              # "Monthly saving x 12"
    c3.metric("Inward rakes over free time", f"{s.in_pct_over_free:.0f}%",
              d(f"{s.in_pct_over_free - b.in_pct_over_free:+.0f} pts"), delta_color="inverse")
    c4.metric("Outward rakes over free time", f"{s.out_pct_over_free:.0f}%",
              d(f"{s.out_pct_over_free - b.out_pct_over_free:+.0f} pts"), delta_color="inverse")
    c5.metric("Tippler wait (median)", f"{s.tippler_median_wait_h:.1f} h",
              d(f"{s.tippler_median_wait_h - b.tippler_median_wait_h:+.1f} h"), delta_color="inverse")

    left, right = st.columns([3, 2])                                            # "Two charts side by side"
    with left:
        st.subheader("Demurrage: July vs your scenario")
        bars = pd.DataFrame({                                                   # "Small table for the bar chart"
            "Flow": ["Inward (unloading)", "Inward (unloading)", "Outward (loading)", "Outward (loading)"],
            "Case": ["July 2025", "Your scenario"] * 2,
            "Rs lakh": [b.in_dem_lakh, s.in_dem_lakh, b.out_dem_lakh, s.out_dem_lakh],
        })
        chart = alt.Chart(bars).mark_bar(cornerRadiusEnd=4).encode(             # "Horizontal bars"
            y=alt.Y("Case:N", title=None, sort=["July 2025", "Your scenario"]),
            x=alt.X("Rs lakh:Q", title="Demurrage per month (Rs lakh)"),
            color=alt.Color("Case:N", scale=alt.Scale(domain=["July 2025", "Your scenario"], range=[GREY, BLUE]),
                            legend=alt.Legend(orient="bottom", title=None)),
            row=alt.Row("Flow:N", title=None, header=alt.Header(labelAngle=0, labelAlign="left")),
            tooltip=["Flow", "Case", alt.Tooltip("Rs lakh:Q", format=".1f")],   # "Hover shows the number"
        ).properties(height=70)
        st.altair_chart(chart, width="stretch")
    with right:
        st.subheader("Range across runs")
        dist = pd.concat([base.assign(Case="July 2025"), scen.assign(Case="Your scenario")])   # "All runs, both cases"
        box = alt.Chart(dist).mark_boxplot(size=40, extent="min-max").encode(  # "Box = middle half of runs"
            x=alt.X("Case:N", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("total_dem_lakh:Q", title="Whole-yard demurrage (Rs lakh)", scale=alt.Scale(zero=False)),
            color=alt.Color("Case:N", scale=alt.Scale(domain=["July 2025", "Your scenario"], range=[GREY, BLUE]), legend=None),
        ).properties(height=300)
        st.altair_chart(box, width="stretch")
        st.caption("Each run replays July with different random work times. The box shows the middle half of runs.")

    with st.expander("See all numbers"):                                       # "Detailed table, folded away"
        tbl = pd.DataFrame({"July 2025 (twin)": b, "Your scenario": s}).round(2)
        tbl.index = tbl.index.str.replace("_", " ")
        st.dataframe(tbl, width="stretch")

with tab2:
    st.subheader("What happened in July 2025")
    k1, k2, k3, k4 = st.columns(4)                                              # "Headline facts"
    k1.metric("Inward rakes", "251", "52% over free time", delta_color="off")
    k2.metric("Outward rakes", "365", "83% over free time", delta_color="off")
    k3.metric("Inward demurrage", "₹38.3 lakh")
    k4.metric("Outward demurrage", "₹107.3 lakh")
    charts = [                                                                  # "Phase 1 charts with a short note"
        ("08_demurrage_inward_vs_outward.png", "Loading costs almost 3x more demurrage than unloading."),
        ("07_outward_over_free_by_mode.png", "Every wagon-loader rake went over free time."),
        ("03_unload_time_manual_vs_tippler.png", "The tippler ran at about one-third of its rated speed."),
        ("02_clustering_vs_demurrage.png", "Rakes arriving in clusters paid over 3x more demurrage."),
        ("05_delay_causes_inward.png", "Bunching and tippler stoppages lead the written causes."),
        ("06_wait_after_drawout.png", "Loaded rakes then waited a median 10.6 h for railway power."),
    ]
    for i in range(0, len(charts), 2):                                          # "Two charts per row"
        cols = st.columns(2)
        for col, (img, note) in zip(cols, charts[i:i + 2]):
            col.image(f"outputs/charts/{img}", width="stretch")
            col.caption(note)

with tab3:
    st.subheader("How the twin works")
    st.markdown("""
- **Rakes arrive** at the real July 2025 hand-over times.
- **Pre-placement steps** (examination, weighment, line clearing) take a time drawn from real July records.
- Each rake **waits for its working point**: 1 tippler, manual unloading lines, silo, wagon loader, manual loading lines.
- A **loco** is needed for every placement and draw-out.
- **Work times** are drawn at random from real July times.
- **Back-loading is linked:** an outward rake can start only when its own inward rake has been drawn out.
- **Demurrage** uses the real slab rule (₹150 per wagon-hour, rising in slabs after 6, 12, 24, 48, 72 hours).
""")
    st.subheader("Does it match reality?")
    val = pd.read_csv("outputs/phase2_validation.csv")                         # "Validation table from Phase 2"
    st.dataframe(val.rename(columns={"measure": "Measure", "actual": "Actual July", "model_mean": "Twin average",
                                     "model_low_5pct": "Twin low (5%)", "model_high_95pct": "Twin high (95%)",
                                     "error_pct": "Error %"}), hide_index=True, width="stretch")
    st.image("outputs/charts/09_validation.png", width=650)
    st.subheader("Honest limits")
    st.markdown("""
- Route conflicts (shared approach lines, hand-operated points, level crossings) are **not yet modelled**, so spreading arrivals shows little gain in this version.
- Shunting moves use a fixed 30 minutes.
- One month of data; savings are model estimates under July traffic, not guarantees.
- All customer, station and site names are anonymised.
""")

st.divider()                                                                    # "Line above the footer"
st.caption("Satish Majji | Beyond the Obvious · Industrial rail & bulk logistics · "
           "Built with Python, SimPy and Streamlit")                           # "Branding footer"
