# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Data quality checks

# COMMAND ----------
dbutils.widgets.text("catalog", "main", "Catalog")
dbutils.widgets.text("schema", "supportsense", "Schema")
dbutils.widgets.text("table", "customer_faq", "Table")
catalog, schema, table = (dbutils.widgets.get(name) for name in ("catalog", "schema", "table"))
target = f"`{catalog}`.`{schema}`.`{table}`"
df = spark.table(target)

# COMMAND ----------
from pyspark.sql import functions as F

required_columns = {
    "document_id", "category", "question", "answer", "source_document",
    "access_classification", "last_updated",
}
missing = required_columns - set(df.columns)
if missing:
    raise ValueError(f"Table is missing required fields: {sorted(missing)}")
duplicate_ids = df.groupBy("document_id").count().filter(F.col("count") > 1).count()
blank_required = df.filter(
    F.col("document_id").isNull() | (F.trim("document_id") == "")
    | F.col("question").isNull() | (F.trim("question") == "")
    | F.col("answer").isNull() | (F.trim("answer") == "")
).count()
invalid_classification = df.filter(~F.col("access_classification").isin("public", "internal", "confidential")).count()
quality = {
    "record_count": df.count(),
    "duplicate_document_ids": duplicate_ids,
    "blank_required_fields": blank_required,
    "invalid_access_classification": invalid_classification,
}
print(quality)
if any(value != 0 for key, value in quality.items() if key != "record_count"):
    raise ValueError("Data quality checks failed; inspect quality output.")

# COMMAND ----------
df.groupBy("category").count().orderBy("category").show(truncate=False)
spark.sql(f"SELECT document_id, category, source_document FROM {target} ORDER BY document_id LIMIT 10").show(truncate=False)
