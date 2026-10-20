# CoCo Agent-mode prompt: approved sandbox recovery

Use only after a human has reviewed the Plan-mode output and explicitly approved the recovery.

```text
Apply the approved correction only in RETAIL_DEMO_COCO_LAB.

Do not modify RETAIL_DEMO, Openflow deployment or runtime configuration, S3 objects, roles,
Metabase production questions, or warehouse settings.

Restore PLAN_DATE as the authoritative merchant-plan business date in the affected sandbox
Dynamic Table. INGESTED_AT remains operational audit metadata. Run only the documented
sandbox recovery validation and report changed objects, validation output, warehouse state,
and rollback steps. Stop after validation.
```
