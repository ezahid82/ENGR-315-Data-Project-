# Analyzing Meteorite Mass, Discovery Methods, and Temporal Patterns in NASA’s Meteorite Landing Dataset

**Team:** The Meteorites  
**Contributors:** Ethan Mallon, Ezhar Zahid, Devon Tremeau  
**Course:** ENGR 315 — Data Project

## Objective and Motivation

This project analyzes NASA’s Meteorite Landings dataset to investigate differences in recorded meteorite mass by discovery status, the relationship between recorded year and mass, and changes in the number of recorded observed falls over time.

The goal is to use descriptive statistics, inferential statistical tests, and clear visualizations to answer the questions below. Results describe the records available in the dataset; they do not by themselves establish causal relationships or measure every meteorite that reaches Earth.

## Dataset

- **Name:** Meteorite Landings
- **Publisher:** NASA Open Data Portal; dataset credited to the Meteoritical Society and collected by Javier de la Torre.
- **Catalog page:** https://data.nasa.gov/dataset/meteorite-landings
- **CSV download:** https://data.nasa.gov/docs/legacy/meteorite_landings/Meteorite_Landings.csv
- **Data.gov listing:** https://catalog.data.gov/dataset/meteorite-landings
- **Key fields:** meteorite name/ID, classification (`recclass`), mass in grams (`mass` or `mass (g)`), discovery status (`fall`), recorded year (`year`), and coordinates (`reclat`, `reclong`).
- **Access date:** Record the date the team downloads the data when finalizing the report.

The script downloads the CSV from the official NASA URL by default. A local CSV can also be supplied. Column names are normalized to support common versions of the dataset.

## Research Questions

### RQ1 — Mass by discovery status
**Question:** Does the average mass of meteorites differ significantly between observed falls and meteorites discovered after landing?

- **Variables:** mass (grams; numeric), fall status (`Fell` or `Found`; categorical).
- **Expected answer form:** group sample sizes, means, medians, spread, mean difference (`Fell − Found`), 95% confidence interval, Welch t-statistic, degrees of freedom, and p-value.
- **Potential benefit:** Helps assess whether recorded meteorites with observed falls have a different mass distribution from meteorites discovered afterward.
- **Hypotheses:** H₀: population mean mass is equal for `Fell` and `Found`. H₁: population mean masses differ.
- **Significance level:** α = 0.05.

### RQ2 — Recorded year and mass
**Question:** Is there a statistically significant relationship between the year a meteorite landed (or was found, for `Found` records) and its mass?

- **Variables:** year (numeric/discrete), mass (grams; numeric).
- **Expected answer form:** Pearson correlation and p-value, Spearman correlation as a robustness check, sample size, and confidence interval for Pearson’s correlation where computable.
- **Potential benefit:** Checks for an association in the historical records and can reveal whether recording or recovery patterns deserve further investigation.
- **Hypotheses:** H₀: no linear association between recorded year and mass. H₁: a linear association exists.
- **Significance level:** α = 0.05.
- **Interpretive caution:** The `year` field is the year of the fall for `Fell` records but may be the discovery year for `Found` records. This is not necessarily a uniform measure of the actual impact year.

### RQ3 — Recorded observed falls over time
**Question:** Has the number of meteorites classified as `Fell` changed significantly over time?

- **Variables:** year (numeric/discrete), count of `Fell` records per year (count).
- **Expected answer form:** annual counts, fitted trend, incidence-rate ratio per year, 95% confidence interval, model p-value, and a dispersion diagnostic.
- **Potential benefit:** Shows whether the dataset’s recorded number of observed falls has changed over time.
- **Hypotheses:** H₀: no temporal trend in expected recorded fall counts. H₁: the expected recorded counts change over time.
- **Significance level:** α = 0.05.
- **Interpretive caution:** Counts reflect observation, documentation, collection, and reporting as well as actual events. They are not a direct count of all meteorites reaching Earth.

## Introduction and Context

The dataset contains catalogued meteorite landings and associated attributes. The `fall` field distinguishes meteorites whose falls were observed (`Fell`) from those discovered after landing (`Found`). Mass is strongly right-skewed in many meteorite datasets, so the analysis will inspect distributions and use log-scaled plots where appropriate. Statistical tests will be interpreted alongside effect sizes, uncertainty, sample sizes, data quality, and limitations.

## Implementation Details: Methods, Metrics, Tools, and Plots

### Shared data preparation

1. Download the official CSV or accept a local CSV file.
2. Normalize column names and map common aliases to `mass`, `fall`, and `year`.
3. Convert mass and year to numeric values; treat invalid/nonpositive mass and invalid/missing year as missing for analyses that require them.
4. Standardize `fall` values by trimming whitespace and normalizing capitalization. Keep only `Fell` and `Found` for RQ1.
5. Report input row count, valid/missing counts for key fields, and the number of records retained by each analysis.
6. Do not silently remove extreme but valid masses. Inspect skew and outliers; use a logarithmic axis for visualization when needed.
7. Save all result tables and figures to `outputs/` so the analysis is reproducible.

### RQ1 method — Welch two-sample t-test

**Preparation:** Keep rows with valid positive mass and a recognized `Fell`/`Found` status.

**Metrics:**
- Sample size per group
- Mean, median, standard deviation, and interquartile range by group
- Difference in means (`Fell − Found`)
- 95% confidence interval for the mean difference
- Welch t-statistic, degrees of freedom, and two-sided p-value

**Tools/packages:** `pandas` for cleaning/group summaries; `numpy` for calculations; `scipy.stats.ttest_ind` for Welch’s test; `matplotlib`/`seaborn` for plots.

**Plots:** Boxplot on a log-scaled mass axis, plus a histogram or ECDF to show skew and overlap. A log axis is for visualization only; the primary test compares means on the original gram scale.

**Decision:** Compare p-value with α = 0.05. Report effect size and confidence interval, not only statistical significance. Because mass is highly skewed and may contain extreme values, describe the sensitivity of the mean to outliers; do not claim that the t-test proves causation.

### RQ2 method — year and mass association

**Preparation:** We Kept rows with valid year and positive mass. We Inspected year range and unusual values before we interpreted trends. 

**Metrics:**
- Number of paired observations
- Pearson correlation coefficient and p-value (primary test of linear association)
- Spearman rank correlation and p-value (robustness check for monotonic association)
- 95% confidence interval for Pearson’s r where computable

**Tools/packages:** `pandas`, `numpy`, `scipy.stats.pearsonr` and `scipy.stats.spearmanr`, `matplotlib`/`seaborn`.

**Plots:** Scatterplot of recorded year versus mass with a logarithmic mass axis; optionally add a trend line. Also inspect year and mass distributions.

**Decision:** Use α = 0.05. Report correlation magnitude, direction, uncertainty, and p-value. Association does not imply causation. Importantly, the year field has different meanings for `Fell` and `Found` records, which can complicate interpretation.

### RQ3 method — annual count trend

**Preparation:** Filter to `fall == "Fell"` and valid years. Convert years to integer calendar years, count records per year, and create a continuous annual sequence over the observed year range so years with no recorded `Fell` rows appear as zero counts. This is a count of records, not proof that no meteorites fell in those years.

**Metrics:**
- Annual recorded `Fell` count
- Poisson regression year coefficient and p-value
- Incidence-rate ratio (IRR) per year and 95% confidence interval
- Pearson dispersion statistic (Pearson χ² / residual degrees of freedom)
- Negative binomial regression as a backup if the Poisson model is overdispersed and the fit is available

**Tools/packages:** `pandas`, `numpy`, `statsmodels` for Poisson and negative binomial GLMs, and `matplotlib`/`seaborn`.

**Plots:** Annual count time series and fitted expected-count trend. A long time range can be hard to read; the report may include a second plot aggregating counts by decade as a descriptive view, while the inferential model remains based on annual counts.

**Decision:** We will use α = 0.05. Report IRR and its confidence interval. If IRR is above 1, the fitted expected recorded count increases per year; below 1, it decreases. We will discuss historical changes in observation, cataloguing, and reporting.

## Repository Structure

```text
.
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   └── README.md
├── docs/
│   └── phase_plan.md
├── src/
│   └── analyze.py
└── outputs/
    ├── figures/
    └── tables/
```

The downloaded dataset and generated outputs are not committed by default. The script writes derived tables and plots into `outputs/`.

## How to Run

Python 3.10 or newer is recommended.

```bash
# 1. Clone the repository
git clone <YOUR_GITHUB_REPO_URL>
cd <YOUR_REPO_FOLDER>

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. Install packages
python -m pip install -r requirements.txt

# 4. Run using the official NASA CSV URL
python src/analyze.py

# Or run using a local dataset file
python src/analyze.py --input data/Meteorite_Landings.csv
```

The script creates CSV tables in `outputs/tables/` and PNG figures in `outputs/figures/`. It prints a concise statistical summary to the terminal. Review the data-quality report and generated output before using results in the report.

## Results (Answers to the Questions)

> **Phase 2 placeholder:** This section will be opulated after running the script and validating the output. 

- RQ1 results: pending analysis.
- RQ2 results: pending analysis.
- RQ3 results: pending analysis.

## Conclusions

> **Placeholder for a later phase.** Evidence for each research question, limitations, and what the results do and do not support will be summarized here.

## Action Items

- [ ] Create the GitHub repository and push these files.\n- [ ] Confirm or adjust task ownership in `docs/team_work_split.md`.
- [ ] Confirm the course-approved dataset version and record the download/access date.
- [ ] Run `python src/analyze.py` and inspect all generated tables and figures.
- [ ] Review potentially erroneous years and document any justified exclusions before final results.
- [ ] Check the `Fell`/`Found` categories and missing values in the downloaded file.
- [ ] Review RQ1’s extreme mass values and discuss the limits of mean-based comparisons.
- [ ] Check RQ3 model diagnostics; use negative binomial regression if Poisson overdispersion is material.
- [ ] Have a second teammate independently review each method and interpretation.
- [ ] Add screenshots/code excerpts if required by the instructor.
- [ ] Write evidence-based results and conclusions after analysis.
- [ ] Prepare final presentation/report and cite the dataset and statistical tools.

**Known risks/issues:** mass is likely highly right-skewed; some rows may have missing/invalid values; the year field has different meanings for `Fell` versus `Found`; observed annual counts depend on reporting and historical documentation; extreme or implausible year values should be investigated rather than silently accepted.

## References / Source Files

1. NASA Open Data Portal, *Meteorite Landings*. https://data.nasa.gov/dataset/meteorite-landings
2. Data.gov, *Meteorite Landings*. https://catalog.data.gov/dataset/meteorite-landings
3. SciPy documentation, `scipy.stats.ttest_ind`, `pearsonr`, and `spearmanr`. https://docs.scipy.org/doc/scipy/
4. pandas documentation. https://pandas.pydata.org/docs/
5. statsmodels documentation, generalized linear models and count models. https://www.statsmodels.org/stable/glm.html
6. Matplotlib documentation. https://matplotlib.org/stable/
7. Seaborn documentation. https://seaborn.pydata.org/

## Team Contributions

Update this section to reflect the work actually completed by each teammate; do not claim work that has not occurred.

- **Ethan Mallon:** [Add assigned tasks and completed contributions]
- **Ezhar Zahid:** [Add assigned tasks and completed contributions]
- **Devon Tremeau:** [Add assigned tasks and completed contributions]
