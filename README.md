# Lean + FLD Manufacturing Simulation

A discrete-event simulation and interactive dashboard reproducing the results of:

> **Kovács, G. (2020)**. Combination of Lean value-oriented conception and facility layout design for even more significant efficiency improvement and cost reduction.  
> *International Journal of Production Research*, 58(10), 2916–2936.

---

## Quick start

```bash
pip install -r requirements.txt
python main.py              # CLI: saves all plots to outputs/
streamlit run app.py        # interactive dashboard
```

## CLI options
```
python main.py --shifts 3   # simulate 3 shifts
python main.py --method sa  # Simulated Annealing for FLD
python main.py --no-plots   # skip figure generation
```

## Key results (Table 3 of paper)
| KPI | Original | Improved | Δ |
|-----|----------|----------|---|
| Productivity | 73 u/shift | 83 u/shift | **+13.7%** |
| Workstations | 14 | 12 | **−14.3%** |
| WIP Inventory | 100% | 64% | **−36%** |
| Material Workflow | 365 UL·m | 348 UL·m | **−4.66%** |
| Travel Distance | 63 m | 55 m | **−12.7%** |
| Space Used | 250 m² | 193.75 m² | **−22.5%** |


