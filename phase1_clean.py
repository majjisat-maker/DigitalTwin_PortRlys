# =============================================================================
# PHASE 1 - DATA FOUNDATION for the Rake Turnaround Digital Twin
# -----------------------------------------------------------------------------
# What this script does, in plain English:
#   1. Reads the raw July rake records (inward unloading + outward loading).
#   2. Cleans them (fixes times, removes broken rows, flags problems).
#   3. Hides real names (customers, stations) so the data is safe to publish.
#   4. Re-calculates demurrage from the contract rules, to check the records.
#   5. Tags each delay remark into simple categories (bunching, tippler, etc.).
#   6. Saves clean CSV files that the simulation (Phase 2) will use.
# Every line has a comment: "English sentence" -> what the Python does.
# =============================================================================

import csv          # "I want to read tab-separated text files" -> load the csv tool
import io           # "Treat a big text string like a file" -> load the io tool
import math         # "I need rounding-up of hours" -> load the math tool
import re           # "I want to find patterns inside text, like 7:30" -> load regex tool
from datetime import datetime   # "I want to work with dates and times" -> load datetime
import pandas as pd             # "I want tables like Excel" -> load pandas, call it pd

RAW_XLSX = "data/raw/july_rake_data.xlsx"   # "Where is the Excel workbook?" -> save its path
SHEET_IN = "Sheet3"                         # "Sheet with all 251 inward rakes"
SHEET_OUT = "ow rly dc"                     # "Sheet with all 365 outward rakes"
from datetime import time, timedelta        # "I also need clock-times and durations"

# ---------------------------------------------------------------------------
# Contract rules for demurrage (taken from the column headings of the data)
# ---------------------------------------------------------------------------
BASE_RATE = 150.0   # "Base charge is Rs 150 per wagon per hour" -> store it
# "Each slab: (from hour, to hour, multiplier of base rate)" -> list of slabs
SLABS = [(0, 6, 1.00), (6, 12, 1.10), (12, 24, 1.25), (24, 48, 1.50), (48, 72, 2.00), (72, 10**6, 3.00)]

# ---------------------------------------------------------------------------
# Small helper functions
# ---------------------------------------------------------------------------
def read_rows(sheet):
    """Read one Excel sheet and return a list of rows (each row = list of cells)."""
    df = pd.read_excel(RAW_XLSX, sheet_name=sheet, header=0)       # "Open the sheet; first row is the heading"
    return df.values.tolist()                                     # "Turn the table into a list of rows"

def to_time(cell):
    """Return a real date-time, or None if the cell is empty or broken."""
    if isinstance(cell, datetime):                                # "If Excel already gives a date-time..."
        return cell                                               # "...use it as it is"
    return None                                                   # "Anything else (blank, '#####') -> nothing"

def to_hours(cell, default):
    """Turn a time like 6:30 (clock, duration or text) into hours, e.g. 6.5."""
    if isinstance(cell, timedelta):                               # "If it is a duration..."
        return cell.total_seconds() / 3600                        # "...seconds / 3600 = hours"
    if isinstance(cell, time):                                    # "If it is a clock-time like 06:30..."
        return cell.hour + cell.minute / 60                       # "...hours + minutes/60"
    m = re.match(r"(\d+):(\d+)", str(cell or ""))                 # "If it is text like '6:30'..."
    return int(m[1]) + int(m[2]) / 60 if m else default           # "...read it, else use the default"

def to_int(cell):
    """Turn 59 or '59' into 59. Return None if it is not a number."""
    try:                                                          # "Try..."
        return int(float(cell))                                   # "...to read it as a whole number"
    except (TypeError, ValueError):                               # "If it fails (blank / text)..."
        return None                                               # "...give back nothing"

def to_float(cell):
    """Turn a cell into a decimal number, 0 if empty."""
    try:
        v = float(cell)                                           # "Read it as a decimal number"
        return 0.0 if v != v else v                               # "Empty Excel cells come as NaN -> make them 0"
    except (TypeError, ValueError):
        return 0.0

def text(cell):
    """Cell as clean text ('' for empty)."""
    return "" if cell is None or (isinstance(cell, float) and cell != cell) else str(cell).strip()  # "NaN -> empty"

def hours_between(start, end):
    """Hours from start to end, e.g. 7.5. None if either time is missing."""
    if start is None or end is None:                              # "If any time is missing..."
        return None                                               # "...we cannot compute"
    return round((end - start).total_seconds() / 3600, 3)         # "Difference in seconds / 3600 = hours"

def demurrage_cost(dem_hours, wagons):
    """Apply the slab rule: each hour is charged at the rate of its slab."""
    cost = 0.0                                                    # "Start the bill at zero" -> cost = 0
    for start, end, mult in SLABS:                                # "Go through each slab one by one"
        hrs_in_slab = max(0, min(dem_hours, end) - start)         # "How many of the hours fall inside this slab?"
        cost += hrs_in_slab * wagons * BASE_RATE * mult           # "Add hours x wagons x rate x multiplier"
    return round(cost, 2)                                         # "Give back the bill rounded to paise"

# "Words in remarks -> delay category" -> a dictionary of keyword lists
DELAY_TAGS = {
    "bunching":          ["bunch"],
    "equipment_tippler": [r"dua?le? mode", r"tippler (is )?stop", r"\bpump", r"\bclamp", r"hopper ja", r"thermostart", r"\boc ?-? ?\d", r"\bbrs\b", r"\blcs\b", r"\bzss\b"],
    "equipment_stacker": [r"stacker", r"conveyor", r"idler", r"skirt rubber", r"pull?e?y", r"power trip", r"33 ?kv"],
    "equipment_loading": ["silo", "bin", "w/ldr", "wagon lodar", "wldr", "chute", "tdg"],
    "previous_rake":     ["empty rake drawn", "empty rake drwan", "d/out of previous", "d/out previous", "after d/out", "previous"],
    "wagon_defect":      ["knuckle", "coupling", "door bend", "bulji", "sick", "air release"],
    "loco_power":        [r"waiting for power", r"powers? (escaped|engaged|not support)", r"loco (pilot|opr|operator|not)", r"\bloco delay"],
    "weather_wet":       ["rain", "wet", "water"],
    "labour_cleaning":   ["cleaning", "labour", "checking"],
    "derailment":        ["derail"],
    "party_owned_rake":  ["owned by", "own rake"],
}

def tag_remark(text):
    """Return the list of delay categories found in a remark."""
    text = (text or "").lower()                                   # "Make the remark lower-case for easy matching"
    found = [tag for tag, words in DELAY_TAGS.items()             # "Keep each category..."
             if any(re.search(w, text) for w in words)]          # "...if any of its patterns appear in the remark"
    return ";".join(found) if found else ("none" if not text.strip() else "other")  # "Join tags with ';'"

def anonymiser(prefix):
    """Create a function that turns real names into 'Prefix-01', 'Prefix-02'..."""
    mapping = {}                                                  # "Empty name book to remember who is who"
    def anon(name):                                               # "The function that does the renaming"
        name = (name or "").strip().upper()                       # "Tidy the real name"
        if not name:                                              # "If there is no name..."
            return ""                                             # "...leave it blank"
        if name not in mapping:                                   # "If we have not seen this name before..."
            mapping[name] = f"{prefix}-{len(mapping) + 1:02d}"    # "...give it the next code, e.g. CUST-03"
        return mapping[name]                                      # "Give back the code"
    anon.mapping = mapping                                        # "Keep the name book so we can save it privately"
    return anon

anon_customer = anonymiser("CUST")     # "Renamer for customers"
anon_station = anonymiser("STN")       # "Renamer for railway stations"

# ---------------------------------------------------------------------------
# 1. INWARD rakes (loaded rakes arriving for unloading)
# ---------------------------------------------------------------------------
rows = read_rows(SHEET_IN)             # "Read all inward rows" -> rows
inward = []                            # "Empty list to collect clean inward rakes"
for r in rows:                                                    # "Look at every row"
    if to_int(r[0]) is None:                                      # "No serial number = total or blank row"
        continue                                                  # "Skip it"
    arr, ho, pt, comp, dout = [to_time(c) for c in r[3:8]]        # "Convert the 5 time columns to date-times"
    wagons_arr = to_int(r[16])                                    # "Wagons that arrived"
    wagons_unl = to_int(r[17])                                    # "Wagons actually unloaded"
    free_h = to_hours(r[21], 6.5)                                 # "Free time in hours; assume 6.5 if missing"
    remark = text(r[25]).replace("\n", " ")                       # "Remarks on one line"
    party_owned = ("owned by" in remark.lower() or "own rake" in remark.lower()  # "Customer's own rake (no demurrage)?"
                   or "GPWIS" in text(r[2]) or text(r[2]).upper().startswith("BLC"))  # "GPWIS and container (BLC) rakes are customer-owned"
    start = ho or arr                                             # "Clock starts at railway hand-over (or arrival)"
    total_h = hours_between(start, dout)                          # "Total hours in our yard"
    dem_h = 0 if (party_owned or total_h is None) else max(0, math.ceil(round(total_h - free_h, 3)))  # "Hours over free time, rounded up"
    recorded_dc = to_float(r[41])                                 # "Bill amount written in the record"
    inward.append({                                               # "Save one clean rake as a dictionary"
        "rake_id": f"IN-{to_int(r[0]):03d}",                      # "Our own ID, e.g. IN-007"
        "rake_type": text(r[2]),                                # "Wagon type, e.g. N BOX"
        "arrival": arr, "handover": ho, "placement": pt,          # "The key time stamps..."
        "completion": comp, "drawout": dout,
        "origin_stn": anon_station(text(r[8])),                         # "Origin station, anonymised"
        "customer": anon_customer(text(r[10])),                   # "Customer, anonymised"
        "mode": text(r[11]).upper(),                            # "MANUAL / TIPPLER / TIPPLER+MANUAL"
        "line": text(r[14]).replace('"', ''),                     # "Unloading line or point"
        "cargo": text(r[15]),                                   # "Cargo type"
        "wagons_arrived": wagons_arr, "wagons_unloaded": wagons_unl,
        "wait_for_placement_h": hours_between(start, pt),         # "Waiting time before placement"
        "unload_h": hours_between(pt, comp),                      # "Unloading time"
        "release_h": hours_between(comp, dout),                   # "Time from completion to draw-out"
        "total_h": total_h,                                       # "Total time in yard"
        "free_h": round(free_h, 2),                               # "Free time allowed"
        "party_owned": party_owned,                               # "True if no demurrage applies"
        "dem_hours_calc": dem_h,                                  # "Demurrage hours we calculated"
        "dem_cost_calc": demurrage_cost(dem_h, wagons_unl or 0),  # "Bill we calculated from the rules"
        "dem_cost_recorded": recorded_dc,                         # "Bill written in the record"
        "delay_tags": tag_remark(remark),                         # "Delay categories from the remark"
        "remark": remark,                                         # "Original remark (no names inside)"
    })

inward = pd.DataFrame(inward)          # "Turn the list into a table"

# ---------------------------------------------------------------------------
# 2. OUTWARD rakes (empty rakes arriving / back-loaded for loading)
# ---------------------------------------------------------------------------
rows = read_rows(SHEET_OUT)            # "Read all outward rows"
outward = []                           # "Empty list for clean outward rakes"
skipped_out = 0                        # "Count rakes we cannot use"
for r in rows:                                                    # "Look at every row"
    if to_int(r[0]) is None:                                      # "No serial number = total or blank row"
        continue                                                  # "Skip it"
    arr, ho, pt, comp, dout = [to_time(c) for c in r[4:9]]        # "Convert the 5 time columns"
    eot, dep = to_time(r[25]), to_time(r[26])                     # "Railway power arrival and departure times"
    if not all([arr, pt, comp, dout]):                            # "If key times are broken..."
        skipped_out += 1                                          # "...count it..."
        continue                                                  # "...and skip this rake"
    free_h = to_hours(r[22], 5.5)                                 # "Free time in hours; assume 5.5 if missing"
    remark = text(r[47]).replace("\n", " ")                       # "Remarks on one line"
    party_owned = "GPWIS" in text(r[3])                           # "Customer-owned rake type"
    start = ho or arr                                             # "Clock starts at hand-over"
    total_h = hours_between(start, dout)                          # "Total time in our yard"
    wagons_ld = to_int(r[18])                                     # "Wagons loaded"
    dem_h = 0 if (party_owned or total_h is None) else max(0, math.ceil(round(total_h - free_h, 3)))  # "Hours over free time"
    recorded_dc = to_float(r[46])                                 # "Recorded bill"
    outward.append({
        "rake_id": f"OUT-{to_int(r[0]):03d}",                     # "Our own ID"
        "flow": "BACKLOAD" if text(r[2]).upper().startswith("BL") else "OUTSIDE_EMPTY",  # "BL = same rake re-loaded; OS = empty from outside"
        "rake_type": text(r[3]),
        "arrival": arr, "handover": ho, "placement": pt, "completion": comp, "drawout": dout,
        "rly_power_arrival": eot, "departure": dep,               # "When railway engine came, when rake left"
        "dest_stn": anon_station(text(r[10])),                          # "Destination, anonymised"
        "customer": anon_customer(text(r[11])),                   # "Customer, anonymised"
        "mode": text(r[12]).upper(),                            # "MANUAL / SILO / W/L (wagon loader) ..."
        "line": text(r[15]).replace('"', ''),
        "cargo": text(r[16]),
        "wagons_arrived": to_int(r[17]), "wagons_loaded": wagons_ld,
        "wait_for_placement_h": hours_between(start, pt),
        "load_h": hours_between(pt, comp),
        "release_h": hours_between(comp, dout),
        "drawout_to_departure_h": hours_between(dout, dep),       # "Waiting for railway after work is done"
        "total_h": total_h,
        "free_h": round(free_h, 2),
        "party_owned": party_owned,
        "dem_hours_calc": dem_h,
        "dem_cost_calc": demurrage_cost(dem_h, wagons_ld or 0),
        "dem_cost_recorded": recorded_dc,
        "delay_tags": tag_remark(remark),
        "remark": remark,
    })

outward = pd.DataFrame(outward)        # "Turn into a table"

# ---------------------------------------------------------------------------
# 3. Quality flags - mark anything suspicious instead of silently deleting it
# ---------------------------------------------------------------------------
for df, work in [(inward, "unload_h"), (outward, "load_h")]:       # "Do the same checks for both tables"
    df["flag"] = ""                                                # "Start with no flags"
    df.loc[df[work] <= 0.25, "flag"] += "work_time_too_short;"     # "Under 15 min of work is not believable"
    df.loc[df[work] > 24, "flag"] += "work_time_over_24h;"         # "Over a day - a special case (e.g. containers)"
    df.loc[df["wait_for_placement_h"] < 0, "flag"] += "negative_wait;"  # "Time going backwards = typing error"
    df.loc[(df["release_h"] - 0.5).abs() < 0.01, "flag"] += "release_is_standard_30min;"  # "Exactly 30 min looks like a fixed entry"
    df.loc[(df["dem_cost_calc"] - df["dem_cost_recorded"]).abs() > 1, "flag"] += "dc_mismatch;"  # "Our bill differs from record"

# ---------------------------------------------------------------------------
# 4. Save results
# ---------------------------------------------------------------------------
inward.drop(columns=["remark"]).to_csv("data/clean/inward_clean.csv", index=False)    # "Public file: no free-text remarks"
outward.drop(columns=["remark"]).to_csv("data/clean/outward_clean.csv", index=False)  # "Public file: no free-text remarks"
inward.to_csv("data/raw/inward_with_remarks_PRIVATE.csv", index=False)               # "Private file: keeps remarks"
outward.to_csv("data/raw/outward_with_remarks_PRIVATE.csv", index=False)             # "Private file: keeps remarks"
pd.DataFrame(                                                                         # "Private name book - never publish"
    [("customer", k, v) for k, v in anon_customer.mapping.items()] +
    [("station", k, v) for k, v in anon_station.mapping.items()],
    columns=["type", "real_name", "code"]).to_csv("data/raw/name_mapping_PRIVATE.csv", index=False)

print(f"Inward rakes cleaned : {len(inward)}")    # "Tell me how many inward rakes we kept"
print(f"Outward rakes cleaned: {len(outward)} (skipped {skipped_out} with broken times)")  # "How many outward rakes we kept"
