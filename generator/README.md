# Deterministic data generator

The generator consumes a qualified TPC-DS cohort and creates only the operational facts missing from
TPC-DS. It never invents item or store identities.

## Input contract

`--cohort` must contain:

- `scenario.json` or one-row `scenario.parquet`;
- `items.parquet` with 20 selected TPC-DS items;
- `stores.parquet` with 25 selected TPC-DS stores;
- `item_store_baseline.parquet` with observed item/store demand and economics.

Snowflake unloads uppercase column names; the loader normalizes them to lowercase. It rejects unknown
keys, duplicate pairs, non-positive demand, wrong item/store counts, and a cohort too sparse to select
three items sharing eight stores.

## Run

```bash
python generator/generate.py --config config/scenario.yaml --cohort data/cohort
python generator/validate.py --config config/scenario.yaml --cohort data/cohort
```

Variation is derived from SHA-256 over the fixed seed and business keys. `manifest.json` records row
counts, bytes, affected keys, and a logical digest per file. Parquet bytes can vary when the Arrow
writer version changes; logical digests remain the reproducibility contract.

The generator will not overwrite an existing output directory without `--force`. Generated files
are ignored by Git.
