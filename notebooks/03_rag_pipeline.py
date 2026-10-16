# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Demonstrate authorized knowledge-base retrieval
# MAGIC This notebook shows a transparent lexical baseline, not Vector Search. Use Vector Search only when provisioned and authorized.

# COMMAND ----------
dbutils.widgets.text("catalog", "main", "Catalog")
dbutils.widgets.text("schema", "supportsense", "Schema")
dbutils.widgets.text("table", "customer_faq", "Table")
catalog, schema, table = (dbutils.widgets.get(name) for name in ("catalog", "schema", "table"))
target = f"`{catalog}`.`{schema}`.`{table}`"
faq = spark.table(target)

# COMMAND ----------
from pyspark.sql import functions as F

question = "What is your refund policy?"
user_role = "public"
query_terms = ["refund", "policy"]

# Server-side authorization filter is applied before search. Do not trust a UI-supplied role
# in a production system; derive identity and entitlements from trusted authentication.
authorized = faq.filter(F.col("access_classification") == user_role)
condition = None
for term in query_terms:
    term_condition = (
        F.lower(F.concat_ws(" ", "category", "question", "answer")).contains(term)
    )
    condition = term_condition if condition is None else (condition | term_condition)
matches = authorized.filter(condition).select(
    "document_id", "question", "answer", "source_document", "last_updated",
)
display(matches.limit(3))

# COMMAND ----------
# Grounded baseline: display the top matching approved answer and its source.
# Local application uses a small TF-IDF-like lexical scorer and abstains below threshold.
match = matches.first()
if match:
    print(f"Answer: {match['answer']}")
    print(f"Source: {match['source_document']} ({match['document_id']})")
else:
    print("I couldn't find that information in the authorized support knowledge base.")
