# Databricks notebook source
# MAGIC %md
# MAGIC # India Post Pincode Directory Bronze to Silver
# MAGIC
# MAGIC Load `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.india_post_pincode_directory`
# MAGIC into `FacilityTrustDesk.virtue_silver.india_post_pincode_directory`.
# MAGIC
# MAGIC Applies postal and location normalization only.

# COMMAND ----------

from pyspark.sql import functions as F

dbutils.widgets.text("source_catalog", "databricks_virtue_foundation_dataset_dais_2026")
dbutils.widgets.text("source_schema", "virtue_foundation_dataset")
dbutils.widgets.text("source_table", "india_post_pincode_directory")
dbutils.widgets.text("target_catalog", "FacilityTrustDesk")
dbutils.widgets.text("target_schema", "virtue_silver")
dbutils.widgets.text("target_table", "india_post_pincode_directory")

source_catalog = dbutils.widgets.get("source_catalog")
source_schema = dbutils.widgets.get("source_schema")
source_table = dbutils.widgets.get("source_table")
target_catalog = dbutils.widgets.get("target_catalog")
target_schema = dbutils.widgets.get("target_schema")
target_table = dbutils.widgets.get("target_table")

source_fqn = f"`{source_catalog}`.`{source_schema}`.`{source_table}`"
target_fqn = f"`{target_catalog}`.`{target_schema}`.`{target_table}`"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{target_catalog}`.`{target_schema}`")


def nullify_empty(col):
    return F.when(F.trim(col) == "", F.lit(None)).otherwise(col)


def clean_text(col):
    cleaned = F.regexp_replace(
        F.regexp_replace(F.trim(F.regexp_replace(col, r"[\x00-\x1f\x7f]", " ")), r"\s+", " "),
        r"\s+",
        " ",
    )
    return F.when(col.isNull(), F.lit(None)).otherwise(nullify_empty(cleaned))


def initcap_digits_removed(col):
    return F.when(
        col.isNull(),
        F.lit(None),
    ).otherwise(
        nullify_empty(
            F.initcap(
                F.regexp_replace(
                    F.regexp_replace(F.trim(F.regexp_replace(col, r"[\x00-\x1f\x7f]", " ")), r"\s+", " "),
                    r"\d+",
                    "",
                )
            )
        )
    )


df = spark.table(source_fqn)

silver_df = (
    df
    .withColumn("circlename", clean_text(F.col("circlename")))
    .withColumn("regionname", clean_text(F.col("regionname")))
    .withColumn("divisionname", clean_text(F.col("divisionname")))
    .withColumn("officename", initcap_digits_removed(F.col("officename")))
    .withColumn(
        "pincode",
        F.when((F.col("pincode") >= 100000) & (F.col("pincode") <= 999999), F.col("pincode")).otherwise(F.lit(None)),
    )
    .withColumn("officetype", initcap_digits_removed(F.col("officetype")))
    .withColumn("delivery", initcap_digits_removed(F.col("delivery")))
    .withColumn(
        "district",
        F.when(
            F.lower(F.trim(F.col("district"))) == F.lit("24 paraganas south"),
            F.lit("South 24 Parganas"),
        )
        .when(
            F.lower(F.trim(F.col("district"))) == F.lit("24 paraganas north"),
            F.lit("North 24 Parganas"),
        )
        .when(
            F.lower(F.trim(F.col("district"))) == F.lit("kaimur (bhabua)"),
            F.lit("Kaimur"),
        )
        .otherwise(
            nullify_empty(
                F.initcap(
                    F.regexp_replace(
                        F.regexp_replace(F.trim(F.regexp_replace(F.col("district"), r"[\x00-\x1f\x7f]", " ")), r"\s+", " "),
                        r"\d+",
                        "",
                    )
                )
            )
        ),
    )
    .withColumn(
        "city_name",
        F.when(
            F.lower(F.trim(F.col("district"))) == F.lit("kaimur (bhabua)"),
            F.lit("Bhabua"),
        ).otherwise(F.lit(None)),
    )
    .withColumn("statename", initcap_digits_removed(F.col("statename")))
    .withColumn("latitude", clean_text(F.col("latitude")))
    .withColumn("longitude", clean_text(F.col("longitude")))
)

(
    silver_df
    .write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(target_fqn)
)

display(
    spark.sql(
        f"""
        SELECT
          COUNT(*) AS total_rows,
          COUNT_IF(pincode BETWEEN 100000 AND 999999) AS valid_pincode_rows,
          COUNT_IF(city_name = 'Bhabua') AS kaimur_rows_with_city_name
        FROM {target_fqn}
        """
    )
)

# COMMAND ----------

display(
    spark.sql(
        f"""
        SELECT district, city_name, statename, pincode, officename
        FROM {target_fqn}
        WHERE city_name = 'Bhabua' OR district = 'Kaimur'
        LIMIT 10
        """
    )
)
