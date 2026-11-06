"""Create static figures from the reproduced CSV outputs."""
import csv
from pathlib import Path

def read_rows(path):
    with path.open(encoding="utf-8",newline="") as handle:return list(csv.DictReader(handle))

def make_plots(output_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output_dir=Path(output_dir);figures=output_dir/"figures";figures.mkdir(parents=True,exist_ok=True)
    daily=read_rows(output_dir/"daily_comparison.csv")
    fig,ax=plt.subplots(figsize=(9,4.8))
    bars=ax.bar([int(r["day"]) for r in daily],[float(r["savings_percent"]) for r in daily],color="#2563EB")
    for bar in bars:ax.annotate(f"{bar.get_height():.2f}%",(bar.get_x()+bar.get_width()/2,bar.get_height()),xytext=(0,5),textcoords="offset points",ha="center")
    ax.set(xlabel="Price day",ylabel="Electricity cost savings (%)",title="Identical 29-unit demand with 5-minute setups",ylim=(0,2.5));ax.set_axisbelow(True);ax.grid(axis="y",alpha=.2)
    fig.tight_layout();fig.savefig(figures/"daily_savings_comparison.png",dpi=200);plt.close(fig)
    rows=read_rows(output_dir/"workload_price_day_results.csv")
    values=[[float(next(r["savings_percent"] for r in rows if int(r["workload_level"])==level and int(r["day"])==day)) for day in range(1,7)] for level in range(1,6)]
    util=[float(next(r["processing_utilization_percent"] for r in rows if int(r["workload_level"])==level)) for level in range(1,6)]
    fig,ax=plt.subplots(figsize=(10,5.2));image=ax.imshow(values,cmap="YlGnBu",aspect="auto",vmin=0,vmax=max(map(max,values)))
    for i,line in enumerate(values):
        for j,value in enumerate(line):
            rgba=image.cmap(image.norm(value));brightness=.2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]
            ax.text(j,i,f"{value:.2f}%",ha="center",va="center",color="white" if brightness<.5 else "black")
    ax.set_xticks(range(6),[f"Day {i}" for i in range(1,7)]);ax.set_yticks(range(5),[f"{u:.2f}%" for u in util]);ax.set(xlabel="Price day",ylabel="Processing utilization",title="Workload and price-day sensitivity\nFixed product mix 2:3:1 — 5-minute setups")
    fig.colorbar(image,ax=ax,label="Savings versus reference plan (%)");fig.tight_layout();fig.savefig(figures/"workload_price_day_heatmap.png",dpi=200);plt.close(fig)
    benchmark=read_rows(output_dir/"grouped_vs_flexible_comparison.csv")
    fig,ax=plt.subplots(figsize=(9,4.8));days=[int(r["day"]) for r in benchmark]
    original=[(float(r["original_reference_cost_eur"])-float(r["flexible_cost_eur"]))/float(r["original_reference_cost_eur"])*100 for r in benchmark]
    improved=[float(r["additional_savings_percent"]) for r in benchmark]
    ax.bar([d-.18 for d in days],original,width=.36,label="Versus original fixed order",color="#2563EB");ax.bar([d+.18 for d in days],improved,width=.36,label="Versus best grouped order at 07:00",color="#D97706")
    ax.set_xticks(days);ax.set(xlabel="Price day",ylabel="Electricity cost savings (%)",title="Effect of benchmark selection",ylim=(0,2.5));ax.legend();ax.set_axisbelow(True);ax.grid(axis="y",alpha=.2)
    fig.tight_layout();fig.savefig(figures/"benchmark_comparison.png",dpi=200);plt.close(fig)
    print("Saved three figures to",figures)

if __name__=="__main__":make_plots(Path(__file__).resolve().parents[1]/"results")
