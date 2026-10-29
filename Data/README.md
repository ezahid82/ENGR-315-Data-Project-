# Data directory

The analysis script downloads the official NASA CSV by default. To use a local copy, place it in this directory and run:

```bash
python src/analyze.py --input data/Meteorite_Landings.csv
```

Official source: https://data.nasa.gov/docs/legacy/meteorite_landings/Meteorite_Landings.csv

The raw CSV is ignored by Git to keep the repository lightweight and avoid committing a separate copy of the source dataset. We will record the data downloaded in the final report
