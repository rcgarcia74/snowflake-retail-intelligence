# 04 — Generate supplemental operational data

The generator uses a cryptographic digest of the fixed seed and business keys for variation. It does
not depend on Python's randomized hash state or an AI model, and it emits logical checksums for every
dataset.

```bash
python generator/generate.py \
  --config config/scenario.yaml \
  --cohort data/cohort \
  --output generated

python generator/validate.py \
  --config config/scenario.yaml \
  --cohort data/cohort \
  --output generated

python scripts/estimate_volume.py --output generated
```

Generation refuses to replace `generated/` unless `--force` is supplied. Validation must report
`PASS` for all checks before upload.

## Output

```text
generated/
├── manifest.json
├── validation_report.json
├── history/
│   ├── inventory_history/part-00000.parquet
│   ├── purchase_order_history/part-00000.parquet
│   └── supplier_performance_history/part-00000.parquet
├── openflow/
│   ├── supplier/supplier.jsonl
│   ├── current_purchase_orders/purchase_orders.jsonl
│   ├── current_receipts/receipts.jsonl
│   └── merchant_plan/merchant_plan.jsonl
└── streaming/
    ├── store_sales_events.jsonl
    └── store_inventory_events.jsonl
```

The history covers 90 complete days immediately before the seven-day hot window. The hot event logs
are globally chronological, which lets the producer stop at a healthy checkpoint and resume into the
failure phase.

## Expected volume

With 500 observed pairs, inventory history has 45,000 rows; weekly PO history has roughly 6,500;
supplier history has 450; the two event streams contain 7,000 rows combined. Openflow feeds are
small. Compression and low-cardinality columns usually keep the output far below 100 MB. The
configured ceiling turns an accidental explosion into a failure rather than a surprise bill.

CoCo may review generator output and help debug schema mismatches. It should not produce the rows,
rewrite manifest values, or bypass a validation failure.

Next: [S3 and Iceberg](05-s3-and-iceberg.md).
