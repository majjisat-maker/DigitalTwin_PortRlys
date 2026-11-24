# =============================================================================
# PHASE 2 - THE SIMULATION TWIN (SimPy)
# -----------------------------------------------------------------------------
# Plain English: we build a "virtual yard" in the computer.
#   - Rakes arrive at the same times as in July 2025.
#   - Each rake waits for its unloading / loading point (tippler, manual line,
#     silo, wagon loader) and for a loco, exactly like the real yard.
#   - Work times are drawn at random from the real July times.
#   - After unloading, back-loaded rakes go on to be loaded (the real cycle).
#   - At the end we calculate demurrage with the real contract rule.
# Running this many times shows the normal range of results, not one guess.
# =============================================================================

import random                                   # "I need random draws" -> random tool
from dataclasses import dataclass, field        # "I want a neat box of settings" -> dataclass
import numpy as np                              # "Maths on lists of numbers" -> numpy
import pandas as pd                             # "Tables" -> pandas
import simpy                                    # "The simulation engine" -> simpy

TIMES = ["arrival", "handover", "placement", "completion", "drawout"]   # "Time columns in our clean data"
SLABS = [(0, 6, 1.00), (6, 12, 1.10), (12, 24, 1.25), (24, 48, 1.50), (48, 72, 2.00), (72, 10**6, 3.00)]  # "Demurrage slabs"
BASE_RATE = 150.0                               # "Rs 150 per wagon per hour"

# ---------------------------------------------------------------------------
# 1. Settings for one run (a "scenario")
# ---------------------------------------------------------------------------
@dataclass
class Scenario:
    name: str = "Baseline (July 2025)"          # "A label for the results"
    locos: int = 9                              # "Locos available (10 minus 1 in maintenance)"
    tippler_count: int = 1                      # "Only one tippler"
    manual_unload_lines: int = 5                # "Up to 5 manual unloading lines at once"
    silo_lines: int = 2                         # "Silo can serve 2 rakes (seen in July)"
    wagon_loader_lines: int = 2                 # "Wagon loader lines (seen in July)"
    manual_load_lines: int = 6                  # "Manual loading lines (seen in July)"
    tippler_speed_factor: float = 1.0           # "1.0 = July speed; 1.5 = 50% faster tipping"
    tippler_block_share: float = 0.70           # "Share of tippler time that blocks the next rake (calibrated to July)"
    inward_work_calib: float = 0.85             # "Recorded inward times are padded up to free time; scale them to true times (calibrated)"
    loading_speed_factor: float = 1.0           # "1.0 = July speed for loading"
    placement_cut_h: float = 0.0                # "Hours saved in the pre-placement steps"
    smooth_inward_arrivals: bool = False        # "True = spread each day's rakes evenly"
    shunt_h: float = 0.5                        # "Loco time for one shunting move"
    release_h: float = 0.5                      # "Completion to draw-out (site standard)"

# ---------------------------------------------------------------------------
# 2. Read July data and build the "pools" of real times to draw from
# ---------------------------------------------------------------------------
def load_data(folder="data/clean"):
    """Read the clean July data and prepare everything the model needs."""
    inw = pd.read_csv(f"{folder}/inward_clean.csv", parse_dates=TIMES)          # "Inward rakes"
    out = pd.read_csv(f"{folder}/outward_clean.csv",
                      parse_dates=TIMES + ["rly_power_arrival", "departure"])  # "Outward rakes"
    for df in (inw, out):                                                        # "For both tables..."
        df["start"] = df["handover"].fillna(df["arrival"])                       # "...the clock starts at hand-over"
    inw["point"] = np.where(inw["mode"].str.contains("TIPPLER"), "tippler", "manual_unload")  # "Which kind of unloading point?"
    out["point"] = out["mode"].map(lambda m: "silo" if m.startswith("SILO") else         # "Which kind of loading point?"
                                   ("wagon_loader" if m.startswith("W/L") else "manual_load"))

    # Link each back-loaded outward rake to the inward rake it came from.
    bl = out[out["flow"] == "BACKLOAD"].merge(inw[["rake_id", "drawout"]].rename(columns={"rake_id": "in_id"}),
                                              left_on="start", right_on="drawout", how="left",
                                              suffixes=("", "_in"))                # "Same time = same rake"
    bl = bl.drop_duplicates("rake_id").drop_duplicates("in_id")                   # "One-to-one links only"
    out["linked_inward"] = out["rake_id"].map(dict(zip(bl["rake_id"], bl["in_id"])))  # "Write the link on each outward rake"

    # Pools of real July times (the model draws from these at random).
    tip = inw[inw.point == "tippler"].sort_values("placement").copy()            # "Tippler rakes in order"
    prev_done = tip["completion"].cummax().shift(1)                              # "When the tippler became free"
    tip_start = pd.concat([tip["placement"], prev_done], axis=1).max(axis=1)     # "Tipping starts after both"
    tip_work = ((tip["completion"] - tip_start).dt.total_seconds() / 3600)        # "Pure tipping hours"
    pools = {
        "tippler": tip_work[tip_work > 0.5].values,                              # "Real tipping times"
        "manual_unload": inw.loc[inw.point == "manual_unload", "unload_h"].clip(0.5, 24).values,  # "Real manual unloading times"
        "silo": out.loc[out.point == "silo", "load_h"].clip(0.5, 24).values,      # "Real silo loading times"
        "wagon_loader": out.loc[out.point == "wagon_loader", "load_h"].clip(0.5, 24).values,
        "manual_load": out.loc[out.point == "manual_load", "load_h"].clip(0.5, 24).values,
        # "Pre-placement steps (examination, weighment, line clearing) when NOT queueing"
        "prep_in": inw.loc[inw.point == "manual_unload", "wait_for_placement_h"].clip(0.25, 12).values,
        "prep_out": out["wait_for_placement_h"].clip(0.25, 12).values,
    }
    return inw, out, pools

# ---------------------------------------------------------------------------
# 3. Demurrage rule
# ---------------------------------------------------------------------------
def demurrage(total_h, free_h, wagons, owned):
    """Return (demurrage hours, rupees) using the real slab rule."""
    if owned:                                                                    # "Customer-owned rakes pay nothing"
        return 0, 0.0
    hrs = max(0, int(np.ceil(round(total_h - free_h, 3))))                       # "Hours over free time, rounded up"
    cost = sum(max(0, min(hrs, e) - s) * wagons * BASE_RATE * m for s, e, m in SLABS)  # "Add each slab's share"
    return hrs, cost

# ---------------------------------------------------------------------------
# 4. One simulation run
# ---------------------------------------------------------------------------
def run_once(inw, out, pools, sc: Scenario, seed=0):
    """Play July once in the virtual yard. Returns one row per rake."""
    rng = random.Random(seed)                                                    # "Own random generator (repeatable)"
    env = simpy.Environment()                                                    # "The virtual clock"
    t0 = min(inw["start"].min(), out["start"].min())                             # "Time zero = first rake of July"
    hrs = lambda ts: (ts - t0).total_seconds() / 3600                            # "Convert a date-time to model hours"

    locos = simpy.Resource(env, capacity=sc.locos)                               # "The loco fleet"
    points = {                                                                   # "All working points, each with its capacity"
        "tippler": simpy.Resource(env, capacity=sc.tippler_count),
        "manual_unload": simpy.Resource(env, capacity=sc.manual_unload_lines),
        "silo": simpy.Resource(env, capacity=sc.silo_lines),
        "wagon_loader": simpy.Resource(env, capacity=sc.wagon_loader_lines),
        "manual_load": simpy.Resource(env, capacity=sc.manual_load_lines),
    }
    results = []                                                                 # "Where each finished rake is written"
    backload_signal = {}                                                         # "Inward rake id -> event 'I am empty now'"

    def draw(pool):                                                              # "Pick one real July time at random"
        return float(rng.choice(pools[pool]))

    def work_time(point):                                                        # "How long the work takes in this scenario"
        t = draw(point)                                                          # "Start from a real July time"
        if point == "tippler":
            return t / sc.tippler_speed_factor                                   # "Faster tippler -> shorter time"
        if point in ("silo", "wagon_loader", "manual_load"):
            return t / sc.loading_speed_factor                                   # "Faster loading -> shorter time"
        return t                                                                 # "Manual unloading (scaled below)"

    def rake(r, direction, start_h):
        """The life of one rake inside the yard."""
        yield env.timeout(max(0.0, start_h - env.now))                           # "Wait until the rake is handed over"
        t_start = env.now                                                        # "Clock starts"
        prep = draw("prep_in" if direction == "in" else "prep_out")              # "Examination, weighment, line clearing..."
        prep = max(sc.shunt_h, prep - sc.placement_cut_h)                        # "...minus any improvement, never below one shunt"
        yield env.timeout(prep - sc.shunt_h)                                     # "Do the pre-placement steps"
        point = points[r["point"]]                                               # "Which point does this rake need?"
        with point.request() as req:                                             # "Ask for the point..."
            yield req                                                            # "...and wait until it is free"
            with locos.request() as lr:                                          # "Ask for a loco to place the rake"
                yield lr
                yield env.timeout(sc.shunt_h)                                    # "Placement move"
            t_place = env.now                                                    # "Rake is placed"
            w = work_time(r["point"])                                            # "How long the work takes"
            if direction == "in":                                                # "Inward records are padded..."
                w *= sc.inward_work_calib                                        # "...so use the calibrated true time"
            blocking = w * sc.tippler_block_share if r["point"] == "tippler" else w  # "Tippler: only part of it blocks the next rake"
            yield env.timeout(blocking)                                          # "Work that keeps the point busy"
        yield env.timeout(w - blocking)                                          # "Finishing steps after the tippler is released (0 for others)"
        t_done = env.now                                                         # "Work completed"
        with locos.request() as lr:                                              # "Ask for a loco to draw the rake out"
            yield lr
            yield env.timeout(sc.release_h)                                      # "Draw-out move"
        t_out = env.now                                                          # "Clock stops"
        total = t_out - t_start                                                  # "Hours in the yard"
        wagons = r["wagons_unloaded"] if direction == "in" else r["wagons_loaded"]
        dh, dc = demurrage(total, r["free_h"], wagons or 0, r["party_owned"])    # "Bill for this rake"
        recorded = total if r["party_owned"] else max(total, r["free_h"])        # "Site records early rakes at exactly free time"
        results.append({"rake_id": r["rake_id"], "direction": direction, "point": r["point"],
                        "wait_h": t_place - t_start, "work_h": t_done - t_place, "total_h": total, "recorded_h": recorded,
                        "dem_h": dh, "dem_cost": dc})
        if direction == "in" and r["rake_id"] in backload_signal:                # "If this rake is back-loaded..."
            backload_signal[r["rake_id"]].succeed(env.now)                       # "...tell its outward twin it is empty now"

    def backloaded_rake(r):
        """An outward rake that starts only when its inward rake is drawn out."""
        t_ready = yield backload_signal[r["linked_inward"]]                      # "Wait for the 'empty now' signal"
        yield env.process(rake(r, "out", t_ready))                               # "Then live as an outward rake"

    # Inward arrivals (real July times, or spread evenly within each day)
    starts = inw["start"].copy()                                                 # "Real hand-over times"
    if sc.smooth_inward_arrivals:                                                # "If we test smooth arrivals..."
        day = starts.dt.floor("D")                                               # "...group by calendar day"
        k = starts.groupby(day).rank(method="first") - 1                         # "...order within the day: 0, 1, 2..."
        n = starts.groupby(day).transform("size")                                # "...rakes that day"
        starts = day + pd.to_timedelta(k * 24 / n, unit="h")                     # "...one every 24/n hours"
    for (_, r), s in zip(inw.iterrows(), starts):                                # "Create every inward rake"
        env.process(rake(r, "in", hrs(s)))
    for _, r in out.iterrows():                                                  # "Create every outward rake"
        if isinstance(r["linked_inward"], str):                                  # "Back-loaded: wait for its inward rake"
            backload_signal[r["linked_inward"]] = env.event()
            env.process(backloaded_rake(r))
        else:                                                                    # "Empty from outside: real arrival time"
            env.process(rake(r, "out", hrs(r["start"])))
    env.run()                                                                    # "Play the whole month"
    return pd.DataFrame(results)

# ---------------------------------------------------------------------------
# 5. Many runs -> averages and ranges
# ---------------------------------------------------------------------------
def summarise(df):
    """Key numbers for one run, inward and outward separately."""
    row = {}
    for d, g in df.groupby("direction"):                                         # "For inward and for outward..."
        row[f"{d}_median_total_h"] = g["total_h"].median()                       # "Typical true time in yard"
        row[f"{d}_median_recorded_h"] = g["recorded_h"].median()                 # "Same, written the way the site records it"
        row[f"{d}_pct_over_free"] = (g["dem_h"] > 0).mean() * 100                # "% of rakes paying demurrage"
        row[f"{d}_dem_h"] = g["dem_h"].sum()                                     # "Demurrage hours"
        row[f"{d}_dem_lakh"] = g["dem_cost"].sum() / 1e5                         # "Demurrage in Rs lakh"
    row["total_dem_lakh"] = df["dem_cost"].sum() / 1e5                           # "Whole yard"
    tip = df[df.point == "tippler"]                                              # "Tippler rakes only"
    row["tippler_median_wait_h"] = tip["wait_h"].median()                        # "How long tippler rakes wait"
    return row

def run_many(inw, out, pools, sc, runs=100):
    """Run the scenario many times and return one summary row per run."""
    return pd.DataFrame([summarise(run_once(inw, out, pools, sc, seed=s)) for s in range(runs)])
