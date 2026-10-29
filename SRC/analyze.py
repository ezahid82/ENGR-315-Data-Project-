#!/usr/bin/env python3
"""Reproducible analysis for The Meteorites' ENGR 315 data project."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from scipy import stats

NASA_CSV_URL = (
    "https://data.nasa.gov/docs/legacy/meteorite_landings/"
    "Meteorite_Landings.csv"
)
ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables"
FIGURE_DIR = ROOT / "outputs" / "figures"


def normalize_column_name(name: object) -> str:
    """Normalize common NASA/Socrata column-name variants."""
    return " ".join(str(name).strip().lower().replace("_", " ").split())


def load_data(input_path: str | None) -> pd.DataFrame:
    if input_path:
        path = Path(input_path)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        print(f"Loading local dataset: {path}")
        return pd.read_csv(path, low_memory=False)

    print(f"Downloading NASA CSV: {NASA_CSV_URL}")
    response = requests.get(NASA_CSV_URL, timeout=60)
    response.raise_for_status()
    from io import BytesIO
    return pd.read_csv(BytesIO(response.content), low_memory=False)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    original = {normalize_column_name(c): c for c in df.columns}
    aliases = {
        "mass": ["mass", "mass g", "mass (g)", "mass grams"],
        "fall": ["fall", "fell found", "fall status"],
        "year": ["year", "year date", "date year"],
        "name": ["name", "place"],
        "recclass": ["recclass", "reclass", "type of meteorite"],
        "reclat": ["reclat", "latitude"],
        "reclong": ["reclong", "longitude"],
    }
    rename = {}
    for canonical, candidates in aliases.items():
        for candidate in candidates:
            if candidate in original:
                rename[original[candidate]] = canonical
                break
    out = df.rename(columns=rename).copy()
    required = {"mass", "fall", "year"}
    missing = sorted(required - set(out.columns))
    if missing:
        raise ValueError(
            "Could not identify required columns: "
            + ", ".join(missing)
            + f". Columns found: {list(df.columns)}"
        )
    return out


def prepare_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = standardize_columns(raw)
    df["mass"] = pd.to_numeric(df["mass"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["fall"] = df["fall"].astype("string").str.strip().str.title()

    quality = pd.DataFrame({
        "metric": [
            "raw_rows",
            "missing_or_invalid_mass",
            "nonpositive_mass",
            "missing_or_invalid_year",
            "unrecognized_or_missing_fall_status",
            "valid_positive_mass",
            "valid_year",
        ],
        "value": [
            len(df),
            int(df["mass"].isna().sum()),
            int((df["mass"].notna() & (df["mass"] <= 0)).sum()),
            int(df["year"].isna().sum()),
            int((~df["fall"].isin(["Fell", "Found"])).sum()),
            int((df["mass"].notna() & (df["mass"] > 0)).sum()),
            int(df["year"].notna().sum()),
        ],
    })
    return df, quality


def save_table(df: pd.DataFrame, filename: str) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLE_DIR / filename, index=False)


def save_figure(filename: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / filename, dpi=180, bbox_inches="tight")
    plt.close()


def q1_mass_by_fall(df: pd.DataFrame) -> dict:
    subset = df.loc[
        df["fall"].isin(["Fell", "Found"])
        & df["mass"].notna()
        & (df["mass"] > 0),
        ["fall", "mass"],
    ].copy()
    groups = {k: g["mass"].to_numpy(dtype=float)
              for k, g in subset.groupby("fall")}
    if not {"Fell", "Found"}.issubset(groups):
        raise ValueError("RQ1 requires at least one valid Fell and Found mass.")

    rows = []
    for label in ["Fell", "Found"]:
        values = groups[label]
        q1, q3 = np.percentile(values, [25, 75])
        rows.append({
            "fall_status": label,
            "n": len(values),
            "mean_mass_g": np.mean(values),
            "median_mass_g": np.median(values),
            "std_mass_g": np.std(values, ddof=1) if len(values) > 1 else np.nan,
            "q1_mass_g": q1,
            "q3_mass_g": q3,
            "iqr_mass_g": q3 - q1,
        })
    save_table(pd.DataFrame(rows), "rq1_group_summary.csv")

    fell, found = groups["Fell"], groups["Found"]
    test = stats.ttest_ind(fell, found, equal_var=False, nan_policy="omit")
    mean_diff = float(np.mean(fell) - np.mean(found))

    # Welch-Satterthwaite degrees of freedom and CI for mean difference.
    v1, v2 = np.var(fell, ddof=1), np.var(found, ddof=1)
    n1, n2 = len(fell), len(found)
    se = np.sqrt(v1 / n1 + v2 / n2)
    denom = ((v1 / n1) ** 2 / (n1 - 1) if n1 > 1 else np.inf) + (
        (v2 / n2) ** 2 / (n2 - 1) if n2 > 1 else np.inf
    )
    dof = (v1 / n1 + v2 / n2) ** 2 / denom if denom > 0 else np.nan
    crit = stats.t.ppf(0.975, dof) if np.isfinite(dof) else np.nan
    ci_low, ci_high = mean_diff - crit * se, mean_diff + crit * se

    result = {
        "question": "RQ1: mass differs by fall status",
        "n_fell": n1,
        "n_found": n2,
        "mean_fell_g": float(np.mean(fell)),
        "mean_found_g": float(np.mean(found)),
        "mean_difference_fell_minus_found_g": mean_diff,
        "ci95_low_g": float(ci_low),
        "ci95_high_g": float(ci_high),
        "welch_t": float(test.statistic),
        "welch_df": float(dof),
        "p_value": float(test.pvalue),
        "alpha": 0.05,
        "significant_at_0_05": bool(test.pvalue < 0.05),
    }
    save_table(pd.DataFrame([result]), "rq1_welch_t_test.csv")

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(9, 5.5))
    sns.boxplot(data=subset, x="fall", y="mass", order=["Fell", "Found"])
    plt.yscale("log")
    plt.xlabel("Recorded fall status")
    plt.ylabel("Mass (g, logarithmic scale)")
    plt.title("Meteorite mass by recorded fall status")
    save_figure("rq1_mass_by_fall_status.png")

    plt.figure(figsize=(9, 5.5))
    for label in ["Fell", "Found"]:
        vals = groups[label]
        sns.ecdfplot(x=vals, label=label)
    plt.xscale("log")
    plt.xlabel("Mass (g, logarithmic scale)")
    plt.ylabel("Cumulative proportion")
    plt.title("Mass distribution by recorded fall status")
    plt.legend()
    save_figure("rq1_mass_ecdf.png")
    return result


def q2_year_mass(df: pd.DataFrame) -> dict:
    subset = df.loc[
        df["year"].notna() & df["mass"].notna() & (df["mass"] > 0),
        ["year", "mass"],
    ].copy()
    # Correlations require at least three observations and nonconstant variables.
    if len(subset) < 3 or subset["year"].nunique() < 2 or subset["mass"].nunique() < 2:
        raise ValueError("RQ2 needs at least 3 paired observations and variation in both variables.")

    pearson = stats.pearsonr(subset["year"], subset["mass"])
    spearman = stats.spearmanr(subset["year"], subset["mass"], nan_policy="omit")
    r = float(pearson.statistic)
    n = len(subset)
    # Fisher z interval approximation; only defined for |r| < 1 and n > 3.
    if n > 3 and abs(r) < 1:
        z = np.arctanh(r)
        se_z = 1 / np.sqrt(n - 3)
        ci_low, ci_high = np.tanh([z - 1.96 * se_z, z + 1.96 * se_z])
    else:
        ci_low, ci_high = np.nan, np.nan

    result = {
        "question": "RQ2: recorded year associated with mass",
        "n": n,
        "pearson_r": r,
        "pearson_ci95_low_approx": float(ci_low),
        "pearson_ci95_high_approx": float(ci_high),
        "pearson_p_value": float(pearson.pvalue),
        "spearman_rho": float(spearman.statistic),
        "spearman_p_value": float(spearman.pvalue),
        "alpha": 0.05,
        "pearson_significant_at_0_05": bool(pearson.pvalue < 0.05),
    }
    save_table(pd.DataFrame([result]), "rq2_correlations.csv")

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=subset, x="year", y="mass", s=22, alpha=0.45, edgecolor=None)
    plt.yscale("log")
    plt.xlabel("Recorded year")
    plt.ylabel("Mass (g, logarithmic scale)")
    plt.title("Recorded year versus meteorite mass")
    save_figure("rq2_year_vs_mass.png")

    # A binned median is a descriptive aid, not a replacement for the test.
    subset["decade"] = (np.floor(subset["year"] / 10) * 10).astype("Int64")
    binned = subset.groupby("decade", dropna=True).agg(
        n=("mass", "size"),
        median_mass_g=("mass", "median"),
    ).reset_index()
    save_table(binned, "rq2_mass_by_decade_descriptive.csv")
    return result


def q3_fell_count_trend(df: pd.DataFrame) -> dict:
    subset = df.loc[
        (df["fall"] == "Fell") & df["year"].notna(),
        ["year"],
    ].copy()
    subset["year"] = np.floor(subset["year"]).astype(int)
    if subset.empty:
        raise ValueError("RQ3 has no valid records with fall status Fell and a valid year.")

    # Avoid treating obviously out-of-range values as calendar years without review.
    # Keep the full observed range in outputs but flag extremes for human review.
    min_year, max_year = int(subset["year"].min()), int(subset["year"].max())
    counts = subset.groupby("year").size().rename("fell_count").reset_index()
    full_years = pd.DataFrame({"year": np.arange(min_year, max_year + 1, dtype=int)})
    annual = full_years.merge(counts, on="year", how="left")
    annual["fell_count"] = annual["fell_count"].fillna(0).astype(int)
    save_table(annual, "rq3_annual_fell_counts.csv")

    model_result = None
    model_name = "unavailable"
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf

        # Center year to improve numerical stability and make intercept interpretable.
        annual["year_centered"] = annual["year"] - annual["year"].mean()
        poisson = smf.glm(
            formula="fell_count ~ year_centered",
            data=annual,
            family=sm.families.Poisson(),
        ).fit()
        dispersion = float(np.sum(poisson.resid_pearson ** 2) / poisson.df_resid) if poisson.df_resid > 0 else np.nan
        fitted = poisson.predict(annual)
        chosen = poisson
        model_name = "Poisson GLM"
        if np.isfinite(dispersion) and dispersion > 1.5:
            try:
                negative_binomial = smf.glm(
                    formula="fell_count ~ year_centered",
                    data=annual,
                    family=sm.families.NegativeBinomial(),
                ).fit()
                chosen = negative_binomial
                fitted = negative_binomial.predict(annual)
                model_name = "Negative binomial GLM (Poisson dispersion > 1.5)"
            except Exception as exc:
                print(f"WARNING: negative binomial fit failed; retaining Poisson result: {exc}")

        coef = float(chosen.params["year_centered"])
        ci = chosen.conf_int().loc["year_centered"]
        p_value = float(chosen.pvalues["year_centered"])
        irr = float(np.exp(coef))
        irr_low, irr_high = float(np.exp(ci.iloc[0])), float(np.exp(ci.iloc[1]))
        model_result = {
            "question": "RQ3: temporal trend in recorded Fell counts",
            "model": model_name,
            "n_years": len(annual),
            "first_year": min_year,
            "last_year": max_year,
            "poisson_pearson_dispersion": dispersion,
            "year_coefficient": coef,
            "incidence_rate_ratio_per_year": irr,
            "irr_ci95_low": irr_low,
            "irr_ci95_high": irr_high,
            "p_value_year_trend": p_value,
            "alpha": 0.05,
            "significant_at_0_05": bool(p_value < 0.05),
            "note": "Interpret as recorded catalog counts, not all actual meteorite falls.",
        }
        annual["fitted_expected_count"] = np.asarray(fitted)
        save_table(pd.DataFrame([model_result]), "rq3_count_model.csv")
        save_table(annual, "rq3_annual_counts_with_fit.csv")
    except Exception as exc:
        print(f"WARNING: Could not fit count model (install statsmodels/check data): {exc}")
        annual["fitted_expected_count"] = np.nan

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(11, 5.5))
    plt.plot(annual["year"], annual["fell_count"], linewidth=1.1, label="Recorded annual count")
    if annual["fitted_expected_count"].notna().any():
        plt.plot(
            annual["year"], annual["fitted_expected_count"],
            linewidth=2, label=f"Fitted {model_name} trend",
        )
    plt.xlabel("Recorded year")
    plt.ylabel("Number of records classified as Fell")
    plt.title("Recorded meteorite falls per year")
    plt.legend()
    save_figure("rq3_annual_fell_counts.png")

    # Decade aggregation is descriptive only; year-level counts feed the model.
    annual["decade"] = (np.floor(annual["year"] / 10) * 10).astype(int)
    decade = annual.groupby("decade", as_index=False)["fell_count"].sum()
    save_table(decade, "rq3_fell_counts_by_decade_descriptive.csv")

    return model_result or {
        "question": "RQ3: temporal trend in recorded Fell counts",
        "model": "not fitted",
        "first_year": min_year,
        "last_year": max_year,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Optional path to a local NASA meteorite CSV.")
    args = parser.parse_args()

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        raw = load_data(args.input)
        df, quality = prepare_data(raw)
        save_table(quality, "data_quality_report.csv")
        print(f"Loaded {len(raw):,} rows and {len(raw.columns)} columns.")
        print("\nData quality:")
        print(quality.to_string(index=False))

        results = []
        for label, function in [
            ("RQ1", q1_mass_by_fall),
            ("RQ2", q2_year_mass),
            ("RQ3", q3_fell_count_trend),
        ]:
            try:
                result = function(df)
                results.append(result)
                print(f"\n{label} summary:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
            except Exception as exc:
                print(f"\nERROR in {label}: {exc}", file=sys.stderr)

        if results:
            save_table(pd.DataFrame(results), "analysis_summary.csv")
        print(f"\nTables saved to: {TABLE_DIR}")
        print(f"Figures saved to: {FIGURE_DIR}")
        print("Review data-quality warnings, year values, and model assumptions before reporting results.")
        return 0
    except Exception as exc:
        print(f"Analysis failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
