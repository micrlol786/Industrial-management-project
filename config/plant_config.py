"""
Plant configuration data extracted directly from:
Kovács (2020) - Combination of Lean value-oriented conception and
facility layout design for even more significant efficiency improvement
and cost reduction. IJPR 58(10), 2916-2936.
"""

# ─────────────────────────────────────────────
# PRODUCTION PARAMETERS
# ─────────────────────────────────────────────
AVAILABLE_TIME_PER_SHIFT = 450   # minutes
CUSTOMER_DEMAND_PER_SHIFT = 80   # units
TAKT_TIME = AVAILABLE_TIME_PER_SHIFT / CUSTOMER_DEMAND_PER_SHIFT  # 5.625 min

SPECIFIC_MATERIAL_HANDLING_COST = 0.05   # Euro / (UL · m)  [assumed]
SPECIFIC_LABOUR_COST = 150               # Euro / person / shift  [assumed]

# ─────────────────────────────────────────────
# ORIGINAL LAYOUT  (14 workstations)
# ─────────────────────────────────────────────
ORIGINAL_CYCLE_TIMES = {
    1: 4.6, 2: 3.9, 3: 3.4, 4: 3.5,
    5: 5.1, 6: 4.7, 7: 3.2, 8: 3.4,
    9: 6.1, 10: 3.4, 11: 5.2, 12: 4.1,
    13: 5.1, 14: 5.0,
}

# Approximate 2-D positions (metres) derived from Figure 2 of the paper
# Grid cell = 0.5 m × 0.5 m
ORIGINAL_POSITIONS = {
     1: (12.0,  9.0),
     2: (15.5,  9.0),
     3: (19.0,  9.0),
     4: (19.0,  5.5),
     5: (12.0,  5.5),
     6: ( 8.5,  9.0),
     7: (22.5,  1.5),
     8: (19.0,  1.5),
     9: (15.5,  1.5),
    10: (12.0,  1.5),
    11: ( 8.5,  5.5),
    12: ( 8.5,  2.0),
    13: ( 4.0,  5.5),
    14: ( 4.0,  1.5),
}

# Material flow matrix (unit loads per shift) – from paper Section 4.3.2
ORIGINAL_MATERIAL_FLOW = {
    (1, 2): 5, (1, 6): 5,
    (2, 3): 5,
    (3, 4): 5,
    (4, 5): 5,
    (5, 6): 6, (5, 11): 1,
    (6, 12): 11,
    (7, 8): 4,
    (8, 9): 4,
    (9, 10): 4,
    (10, 11): 4,
    (11, 12): 4,
    (12, 13): 15,
    (13, 14): 15,
}

# Fixed workstations (cannot be moved)
FIXED_WORKSTATIONS_ORIGINAL = {1, 5, 6}

# ─────────────────────────────────────────────
# IMPROVED LAYOUT  (12 workstations after Line Balancing)
# ─────────────────────────────────────────────
# WS 4 and WS 7 eliminated; remaining renumbered 1-12
IMPROVED_CYCLE_TIMES = {
    1: 4.6, 2: 5.4, 3: 5.4,
    4: 5.1, 5: 4.7,
    6: 5.4, 7: 5.4, 8: 5.3,
    9: 5.2, 10: 4.1, 11: 5.1, 12: 5.0,
}

# Positions after U-cell redesign – based on Figure 5 of the paper
IMPROVED_POSITIONS = {
     1: (12.0, 10.0),
     2: (15.5, 10.0),
     3: (19.0,  8.0),
     4: (12.0,  6.5),
     5: ( 8.5, 10.0),
     6: (17.5,  3.5),
     7: (16.0,  3.5),
     8: (14.5,  3.5),
     9: (10.0,  3.5),
    10: ( 8.5,  3.5),
    11: ( 8.5,  1.5),
    12: (12.0,  1.5),
}

# Material flow matrix for improved layout
IMPROVED_MATERIAL_FLOW = {
    (1, 2): 5, (1, 5): 15,
    (2, 3): 5,
    (3, 4): 5,
    (4, 5): 6, (4, 10): 11,
    (5, 6): 4,
    (6, 7): 4,
    (7, 8): 4,
    (8, 9): 4,
    (9, 11): 15,
    (11, 12): 15,
}

FIXED_WORKSTATIONS_IMPROVED = {1, 4, 5}

# ─────────────────────────────────────────────
# REPORTED KPIs FROM PAPER (Table 3)
# ─────────────────────────────────────────────
PAPER_RESULTS = {
    "longest_cycle_time":   {"original": 6.1,  "improved": 5.4,    "unit": "min"},
    "productivity":         {"original": 73,   "improved": 83,     "unit": "units/shift"},
    "num_workstations":     {"original": 14,   "improved": 12,     "unit": "pieces"},
    "num_operators":        {"original": 14,   "improved": 12,     "unit": "persons"},
    "wip_inventory":        {"original": 100,  "improved": 64,     "unit": "%"},
    "space_used":           {"original": 250,  "improved": 193.75, "unit": "m²"},
    "material_workflow":    {"original": 365,  "improved": 348,    "unit": "UL·m"},
    "travel_distance":      {"original": 63,   "improved": 55,     "unit": "m"},
    "material_handling_cost": {"original": 100, "improved": 95.34, "unit": "%"},
    "labour_cost":          {"original": 100,  "improved": 85.72,  "unit": "%"},
}
