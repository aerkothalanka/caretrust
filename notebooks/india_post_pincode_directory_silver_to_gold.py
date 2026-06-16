# Databricks notebook source
# MAGIC %md
# MAGIC # India Post Pincode Directory Silver to Gold
# MAGIC
# MAGIC Build a gold-layer postal reference table from `FacilityTrustDesk.virtue_silver.india_post_pincode_directory`.
# MAGIC The gold layer keeps the silver columns intact, adds standardized variants, and includes validation flags
# MAGIC for downstream matching and data quality checks.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql import types as T
import re

dbutils.widgets.text("source_catalog", "FacilityTrustDesk")
dbutils.widgets.text("source_schema", "virtue_silver")
dbutils.widgets.text("source_table", "india_post_pincode_directory")
dbutils.widgets.text("target_catalog", "FacilityTrustDesk")
dbutils.widgets.text("target_schema", "virtue_gold")
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


def canonicalize_name(col):
    return F.when(col.isNull(), F.lit(None)).otherwise(
        nullify_empty(
            F.initcap(
                F.regexp_replace(
                    F.regexp_replace(
                        F.regexp_replace(F.trim(F.regexp_replace(col, r"[\x00-\x1f\x7f]", " ")), r"\s+", " "),
                        r"\s*&\s*",
                        " and ",
                    ),
                    r"\s+",
                    " ",
                )
            )
        )
    )


def canonicalize_district(col):
    cleaned = canonicalize_name(col)
    no_dots = F.regexp_replace(F.coalesce(F.trim(col), F.lit("")), r"\.", "")
    acronym_candidate = F.regexp_replace(no_dots, r"[^A-Za-z]", "")
    return F.when(
        col.isNull(),
        F.lit(None),
    ).otherwise(
        F.when(
            F.lower(F.trim(col)).isin("24 paraganas south", "24 parganas south", "south 24 parganas"),
            F.lit("South 24 Parganas"),
        )
        .when(
            F.lower(F.trim(col)).isin("24 paraganas north", "24 parganas north", "north 24 parganas"),
            F.lit("North 24 Parganas"),
        )
        .when(
            F.lower(F.trim(col)).isin("kaimur (bhabua)", "kaimur"),
            F.lit("Kaimur"),
        )
        .when(
            (F.length(acronym_candidate) <= 5) & (F.length(acronym_candidate) > 0) & F.lower(acronym_candidate).isNotNull(),
            F.upper(acronym_candidate),
        )
        .otherwise(cleaned)
    )


def canonicalize_office_type(col):
    return F.when(col.isNull(), F.lit(None)).otherwise(
        nullify_empty(
            F.when(F.lower(F.trim(col)) == F.lit("h.o."), F.lit("HO"))
             .when(F.lower(F.trim(col)) == F.lit("ho"), F.lit("HO"))
             .when(F.lower(F.trim(col)) == F.lit("s.o."), F.lit("SO"))
             .when(F.lower(F.trim(col)) == F.lit("so"), F.lit("SO"))
             .when(F.lower(F.trim(col)) == F.lit("b.o."), F.lit("BO"))
             .when(F.lower(F.trim(col)) == F.lit("bo"), F.lit("BO"))
             .otherwise(F.initcap(F.regexp_replace(F.regexp_replace(F.trim(col), r"\s+", " "), r"\d+", "")))
        )
    )


def parse_pincode(col):
    digits = F.regexp_extract(F.coalesce(col.cast("string"), F.lit("")), r"(\d{6})", 1)
    return F.when(F.length(digits) == 6, digits.cast("int")).otherwise(F.lit(None))


def parse_decimal(col):
    extracted = F.regexp_extract(F.coalesce(col.cast("string"), F.lit("")), r"(-?\d+(?:\.\d+)?)", 1)
    return F.when(F.length(extracted) > 0, extracted.cast("double")).otherwise(F.lit(None))


alias_rows = [
    ("district", "24 paraganas south", "South 24 Parganas"),
    ("district", "24 parganas south", "South 24 Parganas"),
    ("district", "south 24 parganas", "South 24 Parganas"),
    ("district", "24 paraganas north", "North 24 Parganas"),
    ("district", "24 parganas north", "North 24 Parganas"),
    ("district", "north 24 parganas", "North 24 Parganas"),
    ("district", "kaimur (bhabua)", "Kaimur"),
    ("district", "kaimur", "Kaimur"),
    ("district", "y.s.r.", "YSR"),
    ("district", "ysr", "YSR"),
    ("district", "y s r", "YSR"),
    ("state", "jammu & kashmir", "Jammu And Kashmir"),
    ("state", "jammu and kashmir", "Jammu And Kashmir"),
    ("state", "nct of delhi", "NCT Of Delhi"),
    ("state", "andaman & nicobar islands", "Andaman And Nicobar Islands"),
    ("state", "dadra & nagar haveli and daman & diu", "Dadra And Nagar Haveli And Daman And Diu"),
    ("city", "kaimur (bhabua)", "Bhabua"),
    ("city", "bhabua", "Bhabua"),
]

alias_df = spark.createDataFrame(alias_rows, "alias_type string, alias_value string, canonical_value string")
alias_df = alias_df.withColumn("alias_key", F.lower(F.trim(F.col("alias_value"))))
alias_df.cache()

district_alias_df = alias_df.filter(F.col("alias_type") == "district").select(
    F.col("alias_key").alias("district_alias_key"),
    F.col("canonical_value").alias("district_alias_value"),
)

state_alias_df = alias_df.filter(F.col("alias_type") == "state").select(
    F.col("alias_key").alias("state_alias_key"),
    F.col("canonical_value").alias("state_alias_value"),
)

city_alias_df = alias_df.filter(F.col("alias_type") == "city").select(
    F.col("alias_key").alias("city_alias_key"),
    F.col("canonical_value").alias("city_alias_value"),
)


df = spark.table(source_fqn)

gold_df = (
    df
    .filter(
        ~F.lower(F.trim(F.col("statename"))).isin(
            "the dadra and nagar haveli and daman and diu",
        )
    )
    .withColumn("circlename_standardized", canonicalize_name(F.col("circlename")))
    .withColumn("regionname_standardized", canonicalize_name(F.col("regionname")))
    .withColumn("divisionname_standardized", canonicalize_name(F.col("divisionname")))
    .withColumn("officename_standardized", canonicalize_name(F.col("officename")))
    .withColumn("officetype_standardized", canonicalize_office_type(F.col("officetype")))
    .withColumn("delivery_standardized", canonicalize_name(F.col("delivery")))
    .withColumn("pincode_standardized", parse_pincode(F.col("pincode")))
    .withColumn("latitude_standardized", parse_decimal(F.col("latitude")))
    .withColumn("longitude_standardized", parse_decimal(F.col("longitude")))
    .withColumn("is_valid_pincode", F.col("pincode_standardized").isNotNull())
    .withColumn(
        "is_valid_latitude",
        F.col("latitude_standardized").between(F.lit(-90.0), F.lit(90.0)),
    )
    .withColumn(
        "is_valid_longitude",
        F.col("longitude_standardized").between(F.lit(-180.0), F.lit(180.0)),
    )
    .withColumn(
        "needs_review",
        (~F.col("is_valid_pincode"))
        | F.col("district_standardized").isNull()
        | F.col("statename_standardized").isNull()
        | (~F.col("is_valid_latitude") & F.col("latitude").isNotNull())
        | (~F.col("is_valid_longitude") & F.col("longitude").isNotNull()),
    )
    .withColumn(
        "gold_quality_notes",
        F.concat_ws(
            "; ",
            F.when(~F.col("is_valid_pincode"), F.lit("invalid_pincode")),
            F.when(F.col("district_standardized").isNull(), F.lit("missing_district")),
            F.when(F.col("statename_standardized").isNull(), F.lit("missing_state")),
            F.when(~F.col("is_valid_latitude") & F.col("latitude").isNotNull(), F.lit("invalid_latitude")),
            F.when(~F.col("is_valid_longitude") & F.col("longitude").isNotNull(), F.lit("invalid_longitude")),
        ),
    )
)

gold_df = (
    gold_df
    .withColumn("district_alias_key", F.lower(F.trim(F.col("district"))))
    .join(F.broadcast(district_alias_df), on="district_alias_key", how="left")
    .withColumn(
        "district_standardized",
        F.coalesce(F.col("district_alias_value"), canonicalize_district(F.col("district"))),
    )
    .drop("district_alias_key", "district_alias_value")
    .withColumn("state_alias_key", F.lower(F.trim(F.col("statename"))))
    .join(F.broadcast(state_alias_df), on="state_alias_key", how="left")
    .withColumn(
        "statename_standardized",
        F.coalesce(F.col("state_alias_value"), canonicalize_name(F.col("statename"))),
    )
    .drop("state_alias_key", "state_alias_value")
    .withColumn("city_alias_key", F.lower(F.trim(F.coalesce(F.col("city_name"), F.col("district")))))
    .join(F.broadcast(city_alias_df), on="city_alias_key", how="left")
    .withColumn(
        "city_name_standardized",
        F.coalesce(F.col("city_alias_value"), F.col("city_name")),
    )
    .drop("city_alias_key", "city_alias_value")
    .withColumn(
        "city_name_standardized",
        F.when(F.col("district_standardized") == F.lit("Kaimur"), F.lit("Bhabua")).otherwise(F.col("city_name_standardized")),
    )
)

gold_select_cols = [
    "circlename",
    "regionname",
    "divisionname",
    "officename",
    "pincode",
    "officetype",
    "delivery",
    "district",
    "city_name",
    "statename",
    "latitude",
    "longitude",
    "circlename_standardized",
    "regionname_standardized",
    "divisionname_standardized",
    "officename_standardized",
    "pincode_standardized",
    "officetype_standardized",
    "delivery_standardized",
    "district_standardized",
    "city_name_standardized",
    "statename_standardized",
    "latitude_standardized",
    "longitude_standardized",
    "is_valid_pincode",
    "is_valid_latitude",
    "is_valid_longitude",
    "needs_review",
    "gold_quality_notes",
]

(
    gold_df.select(*gold_select_cols)
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
          COUNT_IF(is_valid_pincode) AS valid_pincode_rows,
          COUNT_IF(needs_review) AS review_rows,
          COUNT_IF(city_name_standardized = 'Bhabua') AS kaimur_rows_with_city_name
        FROM {target_fqn}
        """
    )
)

# COMMAND ----------

display(
    spark.sql(
        f"""
        SELECT
          district,
          district_standardized,
          city_name,
          city_name_standardized,
          statename,
          statename_standardized,
          pincode,
          pincode_standardized,
          needs_review,
          gold_quality_notes
        FROM {target_fqn}
        WHERE needs_review OR city_name_standardized = 'Bhabua'
        LIMIT 15
        """
    )
)
