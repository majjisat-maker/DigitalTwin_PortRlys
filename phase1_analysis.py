# =============================================================================
# PHASE 1 - BASELINE ANALYSIS
# -----------------------------------------------------------------------------
# Plain English: read the clean data, measure how the yard performed in July,
# draw charts, and save the "input numbers" the simulation will need in Phase 2.
# =============================================================================

import json                              # "I want to save numbers in a file" -> json tool
import numpy as np                       # "I want maths on lists of numbers" -> numpy as np
import pandas as pd                      # "I want tables" -> pandas as pd
import matplotlib                        # "I want charts" -> matplotlib
matplotlib.use("Agg")                    # "Draw charts into files, not on a screen"
import matplotlib.pyplot as plt          # "The drawing toolbox" -> plt
from scipy import stats                  # "I want to fit statistical curves" -> stats

BLUE, ORANGE, AQUA, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e"  # "Our chart colours"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,   # "Same quiet style for every chart"
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})

TIMES_IN = ["arrival", "handover", "placement", "completion", "drawout"]                 # "Time columns of inward table"
inw = pd.read_csv("data/clean/inward_clean.csv", parse_dates=TIMES_IN)                   # "Read inward table, times as dates"
out = pd.read_csv("data/clean/outward_clean.csv",
                  parse_dates=TIMES_IN + ["rly_power_arrival", "departure"])             # "Read outward table"
inw["day"] = inw["arrival"].dt.date                                                     # "Which calendar day did it arrive?"
inw["hour"] = inw["arrival"].dt.hour                                                    # "Which hour of the day?"
inw["mode_group"] = inw["mode"].replace({"TIPPLER+MANUAL": "TIPPLER"})                  # "Treat tippler+manual as tippler"
normal = inw[~inw["flag"].fillna("").str.contains("too_short|over_24h")]               # "Leave out the 2 odd rakes for curve fitting"

def describe(series):
    """Median, 90th percentile, mean - rounded to 2 decimals."""
    s = series.dropna()                                                                # "Ignore blanks"
    return {"n": int(len(s)), "median": round(s.median(), 2),                          # "How many, middle value"
            "p90": round(s.quantile(0.9), 2), "mean": round(s.mean(), 2)}              # "90% are below this; average"

def fit_lognormal(series):
    """Fit a lognormal curve (good for 'mostly short, sometimes very long' times)."""
    s = series.dropna()                                                                # "Ignore blanks"
    s = s[s > 0]                                                                       # "Lognormal needs positive numbers"
    shape, loc, scale = stats.lognorm.fit(s, floc=0)                                   # "Find the best-fitting curve"
    ks = stats.kstest(s, "lognorm", args=(shape, loc, scale)).pvalue                   # "How well does it fit? (p > 0.05 = fine)"
    return {"dist": "lognormal", "shape": round(shape, 4), "scale": round(scale, 4), "ks_p": round(ks, 3)}

# ---------------------------------------------------------------------------
# 1. Key numbers
# ---------------------------------------------------------------------------
summary = {                                                                            # "A dictionary of headline numbers"
    "inward_rakes": int(len(inw)),
    "outward_rakes": int(len(out)),
    "inward_rakes_per_day": describe(inw.groupby("day").size()),                       # "Rakes arriving per day"
    "inward_wait_h": describe(inw["wait_for_placement_h"]),                            # "Wait before placement"
    "inward_unload_h_manual": describe(normal.loc[normal.mode_group == "MANUAL", "unload_h"]),
    "inward_unload_h_tippler": describe(normal.loc[normal.mode_group == "TIPPLER", "unload_h"]),
    "inward_total_h": describe(inw["total_h"]),
    "inward_rakes_with_demurrage": int((inw["dem_hours_calc"] > 0).sum()),
    "inward_dem_hours": int(inw["dem_hours_calc"].sum()),
    "inward_dem_cost": float(inw["dem_cost_calc"].sum()),
    "outward_wait_h": describe(out["wait_for_placement_h"]),
    "outward_load_h": describe(out["load_h"]),
    "outward_drawout_to_departure_h": describe(out["drawout_to_departure_h"]),
    "outward_rakes_with_demurrage": int((out["dem_hours_calc"] > 0).sum()),
    "outward_dem_hours": int(out["dem_hours_calc"].sum()),
    "outward_dem_cost": float(out["dem_cost_calc"].sum()),
    "outward_load_h_by_mode": {m: describe(g["load_h"]) for m, g in out.groupby("mode") if len(g) >= 10},
}

# ---------------------------------------------------------------------------
# 2. Simulation inputs (what Phase 2 needs)
# ---------------------------------------------------------------------------
gaps = inw.sort_values("arrival")["arrival"].diff().dt.total_seconds().dropna() / 3600  # "Hours between one arrival and the next"
sim_inputs = {
    "inward_arrivals_per_hour_profile": (inw.groupby("hour").size() / inw["day"].nunique()).round(3).to_dict(),  # "Average arrivals in each hour of day"
    "inward_interarrival_h": describe(gaps),                                           # "Gap between arrivals"
    "inward_mode_share": inw["mode_group"].value_counts(normalize=True).round(3).to_dict(),  # "Share manual vs tippler"
    "inward_unload_manual": fit_lognormal(normal.loc[normal.mode_group == "MANUAL", "unload_h"]),
    "inward_unload_tippler": fit_lognormal(normal.loc[normal.mode_group == "TIPPLER", "unload_h"]),
    "inward_free_hours": 6.5,                                                          # "Contract free time - inward"
    "release_h_assumed": 0.5,                                                          # "Completion to draw-out (recorded as standard)"
    "outward_backload_share": round((out["flow"] == "BACKLOAD").mean(), 3),            # "How many outward rakes are re-used inward rakes"
    "outward_load_by_mode": {m: fit_lognormal(g["load_h"]) for m, g in out.groupby("mode") if len(g) >= 20},
    "outward_drawout_to_departure": fit_lognormal(out["drawout_to_departure_h"]),
    "demurrage_rule": {"base_rate_per_wagon_hour": 150, "slabs": [[0, 6, 1.0], [6, 12, 1.1], [12, 24, 1.25], [24, 48, 1.5], [48, 72, 2.0], [72, None, 3.0]]},
}

# ---------------------------------------------------------------------------
# 3. Delay causes (only rakes that paid demurrage)
# ---------------------------------------------------------------------------
def tag_counts(df):
    """Count how often each delay tag appears among rakes with demurrage."""
    tags = df.loc[df["dem_hours_calc"] > 0, "delay_tags"].fillna("none").str.split(";").explode()  # "One row per tag"
    return tags[~tags.isin(["none", "other", "party_owned_rake"])].value_counts()               # "Drop the empty/odd tags"

in_tags, out_tags = tag_counts(inw), tag_counts(out)                                   # "Count for both tables"
summary["inward_delay_tags"] = in_tags.to_dict()
summary["outward_delay_tags"] = out_tags.to_dict()
summary["inward_dem_rakes_without_reason"] = int(((inw.dem_hours_calc > 0) & inw.delay_tags.isin(["none"])).sum())  # "Paid demurrage but no reason written"

# "Does a busy day cause more demurrage?" -> daily rakes vs daily demurrage hours
daily = inw.groupby("day").agg(rakes=("rake_id", "size"), dem_h=("dem_hours_calc", "sum"))
summary["busy_day_correlation"] = round(daily["rakes"].corr(daily["dem_h"]), 2)       # "Correlation (1 = strong link)"
summary["dem_h_per_rake_on_days_le7"] = round(daily.query("rakes<=7").dem_h.sum() / daily.query("rakes<=7").rakes.sum(), 2)
summary["dem_h_per_rake_on_days_ge10"] = round(daily.query("rakes>=10").dem_h.sum() / daily.query("rakes>=10").rakes.sum(), 2)

# "How much of the bill comes from a few bad rakes?"
top = inw.sort_values("dem_cost_calc", ascending=False)                                # "Sort rakes by bill, biggest first"
summary["inward_top10pct_share_of_cost"] = round(top.head(len(top) // 10)["dem_cost_calc"].sum() / top["dem_cost_calc"].sum(), 3)

# ---------------------------------------------------------------------------
# 4. Charts
# ---------------------------------------------------------------------------
def save(fig, name):
    fig.tight_layout()                                                                 # "Stop labels overlapping"
    fig.savefig(f"outputs/charts/{name}.png", dpi=160)                                 # "Save the picture"
    plt.close(fig)                                                                     # "Free the memory"

# Chart 1 - arrivals by hour of day
fig, ax = plt.subplots(figsize=(8, 3.6))
prof = inw.groupby("hour").size() / inw["day"].nunique()                               # "Average rakes per day in each hour"
ax.bar(prof.index, prof.values, color=BLUE, width=0.8)                                 # "Draw one bar per hour"
ax.set_xlabel("Hour of day (arrival at reception yard)"); ax.set_ylabel("Avg rakes / day")
ax.set_title("Inward rakes arrive round the clock - no quiet window", loc="left", color=INK)
ax.set_xticks(range(0, 24, 2))
save(fig, "01_arrivals_by_hour")

# Chart 2 - short-term clustering vs demurrage
srt = inw.sort_values("arrival").reset_index(drop=True)                                # "Rakes in arrival order"
srt["prev6"] = [((srt.arrival < a) & (srt.arrival >= a - pd.Timedelta(hours=6))).sum()  # "How many rakes came in the 6 h before this one?"
                for a in srt.arrival]
srt["prev6_band"] = srt["prev6"].clip(upper=3).map({0: "0", 1: "1", 2: "2", 3: "3 or more"})  # "Group 3+ together"
clus = srt.groupby("prev6_band").agg(dem=("dem_hours_calc", "mean"), n=("rake_id", "size"))   # "Average demurrage per group"
summary["clustering_dem_h_by_prev6"] = clus.round(2).to_dict()
fig, ax = plt.subplots(figsize=(7, 3.8))
ax.bar(clus.index, clus["dem"], color=BLUE, width=0.6)                                 # "One bar per group"
for x, (d, n) in enumerate(zip(clus["dem"], clus["n"])):                               # "Write value and rake count on top"
    ax.text(x, d + 0.05, f"{d:.2f} h\n({n} rakes)", ha="center", color=MUTED, fontsize=9)
ax.set_xlabel("Other rakes that arrived in the 6 hours before this rake")
ax.set_ylabel("Avg demurrage hours per rake")
ax.set_title("Clustered arrivals, not busy days, drive demurrage", loc="left", color=INK)
ax.set_ylim(0, clus["dem"].max() * 1.3)
save(fig, "02_clustering_vs_demurrage")

# Chart 3 - unloading time, manual vs tippler, with free-time line
fig, ax = plt.subplots(figsize=(8, 3.8))
bins = np.arange(0, 16.5, 0.5)                                                         # "Half-hour buckets up to 16 h"
ax.hist(normal.loc[normal.mode_group == "MANUAL", "unload_h"], bins=bins, color=BLUE, alpha=0.75, label="Manual", edgecolor="#fcfcfb")
ax.hist(normal.loc[normal.mode_group == "TIPPLER", "unload_h"], bins=bins, color=ORANGE, alpha=0.75, label="Tippler", edgecolor="#fcfcfb")
ax.axvline(6.5, color=INK, linestyle="--", linewidth=1.5)                              # "Draw the free-time limit"
ax.text(6.6, ax.get_ylim()[1] * 0.9, "Free time 6:30 h\n(whole stay, not only unloading)", color=MUTED, fontsize=9)
ax.set_xlabel("Unloading time, placement to completion (hours)"); ax.set_ylabel("Number of rakes")
ax.set_title("The tippler is slower than manual unloading in July", loc="left", color=INK)
ax.legend(frameon=False)
save(fig, "03_unload_time_manual_vs_tippler")

# Chart 4 - where the time goes (average hours per stage)
stages = inw.groupby("mode_group")[["wait_for_placement_h", "unload_h", "release_h"]].median()  # "Typical hours per stage"
fig, ax = plt.subplots(figsize=(8, 3.3))
left = np.zeros(len(stages))                                                           # "Start each bar at zero"
for col, colr, lab in [("wait_for_placement_h", MUTED, "Wait for placement"), ("unload_h", BLUE, "Unloading"), ("release_h", AQUA, "Release")]:
    ax.barh(stages.index, stages[col], left=left, color=colr, label=lab, edgecolor="#fcfcfb", linewidth=2)
    left += stages[col].values                                                         # "Next part starts where this one ends"
ax.axvline(6.5, color=INK, linestyle="--", linewidth=1.5)
ax.set_xlabel("Median hours (hand-over to draw-out); dashed line = free time")
ax.set_title("Where a typical inward rake spends its time", loc="left", color=INK)
ax.legend(frameon=False, ncol=3, loc="upper left", bbox_to_anchor=(0, -0.32), fontsize=8)
save(fig, "04_time_by_stage")

# Chart 5 - delay causes
fig, ax = plt.subplots(figsize=(8, 3.8))
nice = {"equipment_tippler": "Tippler stoppages", "previous_rake": "Waiting for previous rake",
        "bunching": "Bunching of rakes", "wagon_defect": "Wagon defects", "equipment_stacker": "Stacker / conveyor",
        "loco_power": "Loco / power", "labour_cleaning": "Cleaning / labour", "weather_wet": "Rain / wet cargo",
        "equipment_loading": "Loading equipment", "derailment": "Derailment"}
t = in_tags.rename(index=nice).sort_values()                                           # "Friendly names, smallest at bottom"
ax.barh(t.index, t.values, color=BLUE, edgecolor="#fcfcfb")
for y, v in enumerate(t.values): ax.text(v + 0.3, y, str(v), va="center", color=MUTED, fontsize=9)  # "Write the count at bar end"
ax.set_xlabel("Inward rakes with demurrage that mention this cause (one rake can have several)")
ax.set_title(f"Why inward rakes went over free time ({summary['inward_dem_rakes_without_reason']} rakes had no reason written)", loc="left", color=INK)
save(fig, "05_delay_causes_inward")

# Chart 6 - the hidden wait after draw-out
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.hist(out["drawout_to_departure_h"].dropna().clip(upper=72), bins=np.arange(0, 74, 2), color=ORANGE, edgecolor="#fcfcfb")
ax.axvline(out["drawout_to_departure_h"].median(), color=INK, linestyle="--", linewidth=1.5)
ax.text(out["drawout_to_departure_h"].median() + 1, ax.get_ylim()[1] * 0.85, f"Median {out['drawout_to_departure_h'].median():.1f} h", color=MUTED)
ax.set_xlabel("Hours from draw-out of loaded rake to departure (capped at 72 h)"); ax.set_ylabel("Number of rakes")
ax.set_title("After loading is finished, rakes still wait for railway power", loc="left", color=INK)
save(fig, "06_wait_after_drawout")


# Chart 7 - outward: share of rakes over free time, by loading method
om = out[out["mode"].isin(["MANUAL", "SILO", "W/L", "W/L+MAN"])].copy()            # "Keep the 4 main loading methods"
om["mode"] = om["mode"].replace({"W/L": "Wagon loader", "W/L+MAN": "Wagon loader + manual", "MANUAL": "Manual", "SILO": "Silo"})
g = om.groupby("mode").agg(over=("dem_hours_calc", lambda x: (x > 0).mean() * 100),  # "% of rakes that paid demurrage"
                           n=("rake_id", "size")).sort_values("over")
summary["outward_pct_over_free_by_mode"] = g.round(1).to_dict()
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.barh(g.index, g["over"], color=ORANGE, edgecolor="#fcfcfb")                     # "One bar per method"
for y, (v, n) in enumerate(zip(g["over"], g["n"])):                                # "Write % and rake count"
    ax.text(v + 1, y, f"{v:.0f}%  ({n} rakes)", va="center", color=MUTED, fontsize=9)
ax.set_xlim(0, 115); ax.set_xlabel("% of outward rakes that went over free time")
ax.set_title(f"Loading: {(out.dem_hours_calc > 0).mean()*100:.0f}% of outward rakes pay demurrage", loc="left", color=INK)
save(fig, "07_outward_over_free_by_mode")

# Chart 8 - where the demurrage money goes
fig, ax = plt.subplots(figsize=(7, 2.6))
money = pd.Series({"Inward (unloading)": inw["dem_cost_calc"].sum() / 1e5, "Outward (loading)": out["dem_cost_calc"].sum() / 1e5})
ax.barh(money.index, money.values, color=[BLUE, ORANGE], edgecolor="#fcfcfb")
for y, v in enumerate(money.values): ax.text(v + 1, y, f"Rs {v:.1f} lakh", va="center", color=MUTED)
ax.set_xlim(0, money.max() * 1.25); ax.set_xlabel("Demurrage in July (Rs lakh)")
ax.set_title("Loading costs almost 3x more demurrage than unloading", loc="left", color=INK)
save(fig, "08_demurrage_inward_vs_outward")

# ---------------------------------------------------------------------------
# 5. Save numbers
# ---------------------------------------------------------------------------
json.dump(summary, open("outputs/baseline_summary.json", "w"), indent=2, default=str)  # "Save headline numbers"
json.dump(sim_inputs, open("outputs/sim_inputs.json", "w"), indent=2, default=str)     # "Save simulation inputs"
print(json.dumps(summary, indent=1, default=str))                                      # "Show results on screen"
print(json.dumps(sim_inputs, indent=1, default=str))
