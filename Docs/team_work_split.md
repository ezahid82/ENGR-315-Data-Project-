# Suggested Team Work Split

Use one shared GitHub repository and short feature branches or separate pull requests. These are suggested assignments; revise them to reflect the team's actual agreement.

## Ethan Mallon — RQ1: Mass by fall status
- Review the `Fell` and `Found` labels and valid mass values.
- Run and independently verify the descriptive summary and Welch t-test.
- Review the log-scale boxplot and ECDF for skew/outliers.
- Draft the RQ1 results paragraph with group sizes, mean difference, 95% CI, and p-value.

## Ezhar Zahid — RQ2: Recorded year and mass
- Review valid year values and document any suspicious dates.
- Run and independently verify Pearson and Spearman correlation results.
- Review the scatterplot and decade summary.
- Draft the RQ2 results paragraph and explain the limitation that `year` means fall year for `Fell` but may mean discovery year for `Found`.

## Devon Tremeau — RQ3: Annual observed-fall counts and integration
- Verify annual `Fell` counts and the count-model output.
- Check Poisson dispersion and whether the negative binomial backup was used.
- Review the annual trend plot and decade-level descriptive table.
- Integrate the methods/results into the README and coordinate final review.

## Shared responsibilities
- All three teammates review the data-quality report and final interpretations.
- Each teammate checks another teammate's calculations or conclusions.
- Do not write numerical findings into the README until the script has been run successfully and outputs have been inspected.
- Keep raw data and generated output files out of Git unless the instructor specifically requests them.
- Use clear commit messages and do not commit secrets, virtual environments, or unrelated files.
