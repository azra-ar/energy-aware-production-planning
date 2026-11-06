"""Reproduce the quantitative analyses from the source JSON."""
import argparse,csv,json,hashlib,platform,importlib.metadata
from pathlib import Path
from itertools import permutations
from .data import load_case, MIX
from .scheduler import optimize_day, grouped_order_cost
from .validation import run_validation

ROOT = Path(__file__).resolve().parents[1]

def write_csv(path, rows):
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)

def analyze(source_path, output_dir):
    output_dir.mkdir(parents=True,exist_ok=True)
    jobs,days,unassigned=load_case(source_path)
    daily=[];setup=[];workload=[];benchmarks=[]
    for day,prices in enumerate(days,1):
        result=optimize_day(jobs,prices,5)
        daily.append({"day":day,**result})
        candidates=[(grouped_order_cost(order,prices,5), " → ".join(j["job_type_id"] for j in order)) for order in permutations(jobs)]
        best_cost,best_order=min(candidates)
        flexible=result["optimized_cost_eur"]
        assert flexible <= best_cost + 1e-8
        benchmarks.append({"day":day,"best_grouped_order":best_order,
            "original_reference_cost_eur":result["reference_cost_eur"],
            "best_grouped_cost_eur":best_cost,"flexible_cost_eur":flexible,
            "additional_savings_eur":best_cost-flexible,
            "additional_savings_percent":(best_cost-flexible)/best_cost*100})
        for level in range(1,6):
            scenario=[{**job,"quantity":MIX[job["job_type_id"]]*level} for job in jobs]
            minutes=sum(j["quantity"]*len(j["profile_wh"])*5 for j in scenario)
            workload.append({"day":day,"workload_level":level,
                "processing_minutes":minutes,"processing_utilization_percent":minutes/960*100,
                **optimize_day(scenario,prices,5)})
    for minutes in [0,5,10,15]:
        setup.append(optimize_day(jobs,days[0],minutes))
    summaries=[]
    for level in range(1,6):
        rows=[r for r in workload if r["workload_level"]==level]
        base=sum(r["reference_cost_eur"] for r in rows)
        optimum=sum(r["optimized_cost_eur"] for r in rows)
        summaries.append({"workload_level":level,
            "processing_utilization_percent":rows[0]["processing_utilization_percent"],
            "total_reference_cost_eur":base,"total_optimized_cost_eur":optimum,
            "combined_savings_percent":(base-optimum)/base*100,
            "min_daily_savings_percent":min(r["savings_percent"] for r in rows),
            "max_daily_savings_percent":max(r["savings_percent"] for r in rows)})
    flat=optimize_day(jobs,[sum(days[0])/len(days[0])]*192,5)
    assert abs(flat["savings_eur"]) < 1e-8
    validations=run_validation()
    write_csv(output_dir/"daily_comparison.csv",daily)
    write_csv(output_dir/"setup_sensitivity.csv",setup)
    write_csv(output_dir/"workload_price_day_results.csv",workload)
    write_csv(output_dir/"workload_summary.csv",summaries)
    write_csv(output_dir/"grouped_vs_flexible_comparison.csv",benchmarks)
    write_csv(output_dir/"algorithm_validation_results.csv",validations)
    processed=ROOT/"data/processed"
    processed.mkdir(parents=True,exist_ok=True)
    write_csv(processed/"selected_products.csv",[{k:v for k,v in j.items() if k!="profile_wh"} for j in jobs])
    price_rows=[{"day":day,"slot_index":i,"start_minutes":420+i*5,"price_eur_per_wh":price,"price_eur_per_kwh":price*1000} for day,prices in enumerate(days,1) for i,price in enumerate(prices)]
    write_csv(processed/"daily_prices.csv",price_rows)
    metadata={"source_doi":"10.5281/zenodo.4106746",
        "source_sha256":hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "machine":"MAQ120","slot_minutes":5,"working_hours":"07:00–23:00",
        "original_selected_quantities":[j["quantity"] for j in jobs],
        "controlled_workload_mix":[2,3,1],"workload_levels":[1,2,3,4,5],
        "setup_scenarios_minutes":[0,5,10,15],"main_setup_minutes":5,
        "initial_setup_minutes":0,"setup_energy_kwh":0,"idle_energy_kwh":0,
        "all_jobs_available_at":"07:00","price_information":"complete day known before scheduling",
        "daily_demand_is_scenario":True,"unassigned_modes_excluded":unassigned,
        "flat_price_check_savings_eur":flat["savings_eur"],
        "independent_validation_tests_passed":len(validations),"python_version":platform.python_version()}
    (output_dir/"run_metadata.json").write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Completed: 6 daily cases, 30 workload cases, 4 setup cases and 6 independent tests.")
    print("Outputs:",output_dir)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",type=Path,default=ROOT/"data/raw/Input_JSON_Schedule_Optimization.json")
    parser.add_argument("--output-dir",type=Path,default=ROOT/"results")
    parser.add_argument("--plots",action="store_true")
    args=parser.parse_args()
    analyze(args.data,args.output_dir)
    if args.plots:
        from .make_plots import make_plots
        make_plots(args.output_dir)

if __name__=="__main__":main()
