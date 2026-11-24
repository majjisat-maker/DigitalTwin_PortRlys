# =============================================================================
# PHASE 2 - VALIDATE THE TWIN, THEN TEST "WHAT-IF" SCENARIOS
# -----------------------------------------------------------------------------
# Plain English:
#   Step 1 - Play July 100 times in the virtual yard and compare with reality.
#   Step 2 - Change one thing at a time (faster tippler, smoother arrivals...)
#            and see how much demurrage changes.
# =============================================================================

import json                                       # "Save results as a file"
from dataclasses import replace                   # "Copy a scenario and change one setting"
import numpy as np                                # "Maths"
import pandas as pd                               # "Tables"
import matplotlib                                 # "Charts"
matplotlib.use("Agg")                             # "Draw into files"
import matplotlib.pyplot as plt                   # "Drawing toolbox"
from rake_twin_sim import Scenario, load_data, run_many   # "Our virtual yard"

RUNS = 100                                        # "How many times to play each scenario"
BLUE, ORANGE, AQUA, INK, MUTED, SURF = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#fcfcfb"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF})

inw, out, pools = load_data()                     # "Read July data and real-time pools"
base = Scenario()                                 # "The calibrated July yard"

# ---------------------------------------------------------------------------
# Step 1 - Validation
# ---------------------------------------------------------------------------
sim = run_many(inw, out, pools, base, runs=RUNS)  # "Play July 100 times"
actual = {                                        # "What really happened in July"
    "in_pct_over_free": (inw.dem_hours_calc > 0).mean() * 100,
    "in_dem_h": inw.dem_hours_calc.sum(),
    "in_dem_lakh": inw.dem_cost_calc.sum() / 1e5,
    "out_median_recorded_h": out.total_h.median(),
    "out_pct_over_free": (out.dem_hours_calc > 0).mean() * 100,
    "out_dem_h": out.dem_hours_calc.sum(),
    "out_dem_lakh": out.dem_cost_calc.sum() / 1e5,
    "total_dem_lakh": (inw.dem_cost_calc.sum() + out.dem_cost_calc.sum()) / 1e5,
}
labels = {"in_pct_over_free": "Inward: % rakes over free time", "in_dem_h": "Inward: demurrage hours",
          "in_dem_lakh": "Inward: demurrage (Rs lakh)", "out_median_recorded_h": "Outward: median hours in yard",
          "out_pct_over_free": "Outward: % rakes over free time", "out_dem_h": "Outward: demurrage hours",
          "out_dem_lakh": "Outward: demurrage (Rs lakh)", "total_dem_lakh": "Whole yard: demurrage (Rs lakh)"}
val = pd.DataFrame([{                             # "One row per measure: actual vs model"
    "measure": labels[k], "actual": round(v, 1),
    "model_mean": round(sim[k].mean(), 1),
    "model_low_5pct": round(sim[k].quantile(0.05), 1),       # "5% of runs were below this"
    "model_high_95pct": round(sim[k].quantile(0.95), 1),     # "5% of runs were above this"
    "error_pct": round((sim[k].mean() - v) / v * 100, 1),     # "How far the average run is from reality"
} for k, v in actual.items()])
val.to_csv("outputs/phase2_validation.csv", index=False)      # "Save the comparison"
print(val.to_string(index=False))

# ---------------------------------------------------------------------------
# Step 2 - What-if scenarios (one change at a time, then combined)
# ---------------------------------------------------------------------------
scenarios = [
    base,
    replace(base, name="Tippler 25% faster", tippler_speed_factor=1.25),
    replace(base, name="Tippler 50% faster", tippler_speed_factor=1.50),
    replace(base, name="Inward arrivals spread evenly", smooth_inward_arrivals=True),
    replace(base, name="Placement steps 30 min quicker", placement_cut_h=0.5),
    replace(base, name="Loading 15% faster", loading_speed_factor=1.15),
    replace(base, name="Only 5 locos (stress test)", locos=5),
    replace(base, name="Combined: tippler +25%, even arrivals, placement -30 min, loading +15%",
            tippler_speed_factor=1.25, smooth_inward_arrivals=True, placement_cut_h=0.5, loading_speed_factor=1.15),
]
rows = []
for sc in scenarios:                                          # "Play every scenario 100 times"
    r = sim if sc is base else run_many(inw, out, pools, sc, runs=RUNS)
    rows.append({
        "scenario": sc.name,
        "inward_lakh": r.in_dem_lakh.mean(), "outward_lakh": r.out_dem_lakh.mean(),
        "total_lakh": r.total_dem_lakh.mean(),
        "total_low": r.total_dem_lakh.quantile(0.05), "total_high": r.total_dem_lakh.quantile(0.95),
        "in_pct_over": r.in_pct_over_free.mean(), "out_pct_over": r.out_pct_over_free.mean(),
        "tippler_wait_h": r.tippler_median_wait_h.mean(),
    })
res = pd.DataFrame(rows).round(2)                             # "Results table"
res["saving_lakh_per_month"] = (res.loc[0, "total_lakh"] - res["total_lakh"]).round(1)   # "Money saved vs baseline"
res["saving_crore_per_year"] = (res["saving_lakh_per_month"] * 12 / 100).round(2)        # "Same, for a year"
res.to_csv("outputs/phase2_scenarios.csv", index=False)
print(res.to_string(index=False))

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
# Chart A - validation: actual vs model (demurrage in lakh)
keys = ["in_dem_lakh", "out_dem_lakh", "total_dem_lakh"]
fig, ax = plt.subplots(figsize=(8, 3.4))
y = np.arange(len(keys))                                      # "One row per measure"
ax.barh(y + 0.2, [actual[k] for k in keys], height=0.38, color=MUTED, label="Actual July 2025")
m = [sim[k].mean() for k in keys]                             # "Model average"
lo = [sim[k].mean() - sim[k].quantile(0.05) for k in keys]    # "Distance to low end"
hi = [sim[k].quantile(0.95) - sim[k].mean() for k in keys]    # "Distance to high end"
ax.barh(y - 0.2, m, height=0.38, color=BLUE, xerr=[lo, hi], ecolor=INK, capsize=3, label="Digital twin (100 runs, 5–95% range)")
ax.set_yticks(y, ["Inward", "Outward", "Whole yard"])
ax.set_xlabel("Demurrage in July (Rs lakh)")
ax.set_title("The twin reproduces July demurrage", loc="left", color=INK)
ax.legend(frameon=False, fontsize=8, loc="lower right")
fig.tight_layout(); fig.savefig("outputs/charts/09_validation.png", dpi=160); plt.close(fig)

# Chart B - scenarios: monthly saving vs baseline
sc_plot = res.iloc[1:].copy()                                 # "Every scenario except the baseline"
sc_plot["short"] = ["Tippler +25%", "Tippler +50%", "Even arrivals", "Placement −30 min",
                    "Loading +15%", "5 locos (stress)", "Combined"]
sc_plot = sc_plot.sort_values("saving_lakh_per_month")       # "Smallest at the bottom"
fig, ax = plt.subplots(figsize=(8, 3.8))
colors = [ORANGE if v < 0 else BLUE for v in sc_plot["saving_lakh_per_month"]]   # "Orange = costs more"
ax.barh(sc_plot["short"], sc_plot["saving_lakh_per_month"], color=colors, edgecolor=SURF)
for yy, v in enumerate(sc_plot["saving_lakh_per_month"]):    # "Write the value at the bar end"
    ax.text(v + (1 if v >= 0 else -1), yy, f"{v:+.1f}", va="center", ha="left" if v >= 0 else "right", color=MUTED, fontsize=9)
ax.axvline(0, color=INK, linewidth=1)
ax.set_xlabel("Demurrage saved per month vs July baseline (Rs lakh)")
ax.set_title("What each change is worth", loc="left", color=INK)
fig.tight_layout(); fig.savefig("outputs/charts/10_scenario_savings.png", dpi=160); plt.close(fig)

json.dump({"runs_per_scenario": RUNS, "calibration": {"tippler_block_share": base.tippler_block_share,
           "inward_work_calib": base.inward_work_calib}}, open("outputs/phase2_settings.json", "w"), indent=2)
