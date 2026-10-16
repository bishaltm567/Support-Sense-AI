# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Load fictional support FAQs into Delta
# MAGIC Configure the catalog/schema through widgets. No credentials are embedded.

# COMMAND ----------
dbutils.widgets.text("catalog", "main", "Unity Catalog catalog")
dbutils.widgets.text("schema", "supportsense", "Schema")
dbutils.widgets.text("source_path", "../data/customer_faq.csv", "CSV path (workspace/repo path)")
dbutils.widgets.text("table", "customer_faq", "Target table")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
source_path = dbutils.widgets.get("source_path")
table = dbutils.widgets.get("table")

if not all(value.replace("_", "").replace("-", "").isalnum() for value in (catalog, schema, table)):
    raise ValueError("Catalog, schema, and table must be simple SQL identifiers.")
target = f"`{catalog}`.`{schema}`.`{table}`"

# COMMAND ----------
raw = spark.read.option("header", True).option("inferSchema", False).csv(source_path)
required = {
    "document_id", "category", "question", "answer", "source_document",
    "access_classification", "last_updated",
}
missing = required - set(raw.columns)
if missing:
    raise ValueError(f"FAQ source is missing required columns: {sorted(missing)}")

from pyspark.sql import functions as F

clean = (
    raw.select(
        F.trim("document_id").alias("document_id"),
        F.trim("category").alias("category"),
        F.trim("question").alias("question"),
        F.trim("answer").alias("answer"),
        F.trim("source_document").alias("source_document"),
        F.lower(F.trim("access_classification")).alias("access_classification"),
        F.to_date("last_updated").alias("last_updated"),
    )
    .dropDuplicates(["document_id"])
    .na.drop(subset=["document_id", "category", "question", "answer", "source_document", "access_classification", "last_updated"])
)
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
clean.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target)
print(f"Loaded {clean.count()} rows into {target}")
display(clean.orderBy("document_id"))

# COMMAND ----------
# Example query
spark.sql(f"SELECT category, COUNT(*) AS faq_count FROM {target} GROUP BY category ORDER BY category").show()
