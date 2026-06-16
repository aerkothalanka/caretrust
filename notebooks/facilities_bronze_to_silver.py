# Databricks notebook source
# MAGIC %md
# MAGIC # Facilities Bronze to Silver
# MAGIC
# MAGIC Load `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities`
# MAGIC into `FacilityTrustDesk.virtue_silver.facilities`.
# MAGIC
# MAGIC Keeps the raw `name` column and adds `Name_Standardized`.

# COMMAND ----------

import re
from pyspark.sql import functions as F
from pyspark.sql import types as T

dbutils.widgets.text("source_catalog", "databricks_virtue_foundation_dataset_dais_2026")
dbutils.widgets.text("source_schema", "virtue_foundation_dataset")
dbutils.widgets.text("source_table", "facilities")
dbutils.widgets.text("target_catalog", "FacilityTrustDesk")
dbutils.widgets.text("target_schema", "virtue_silver")
dbutils.widgets.text("target_table", "facilities")

source_catalog = dbutils.widgets.get("source_catalog")
source_schema = dbutils.widgets.get("source_schema")
source_table = dbutils.widgets.get("source_table")
target_catalog = dbutils.widgets.get("target_catalog")
target_schema = dbutils.widgets.get("target_schema")
target_table = dbutils.widgets.get("target_table")

source_fqn = f"`{source_catalog}`.`{source_schema}`.`{source_table}`"
target_fqn = f"`{target_catalog}`.`{target_schema}`.`{target_table}`"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{target_catalog}`.`{target_schema}`")

FACILITY_ACRONYMS = {
    "ASG",
    "ESI",
    "SRL",
    "SMS",
    "KD",
    "HCG",
    "ECHS",
    "IVF",
    "MRI",
    "CT",
    "PET",
    "ICU",
    "NICU",
    "OPD",
    "ENT",
    "NABH",
    "AIIMS",
    "BMS",
    "24X7",
    "3D",
}

INITIALISM_TOKENS = {
    "DY",
    "DR",
}

JUNK_PREFIXES = (
    "and accountability",
    "located in",
    "the capital of",
    "we offer",
    "this multi-facility",
    "must be in",
    "to specialized procedures",
)


def standardize_facility_name(raw: str | None) -> str | None:
    if raw is None:
        return None

    s = raw.strip()
    for dash in ("–", "—", "‑", "‐", "−"):
        s = s.replace(dash, "-")
    s = re.sub(r"\s+", " ", s)
    s = s.replace("Women S", "Women's").replace("Men S", "Men's")
    s = re.sub(r"\s*-\s*", " - ", s)
    s = re.sub(r"\s+", " ", s).strip()

    lowered = s.lower()
    if len(s) > 20 and (
        re.match(r"^[a-z]", s) or any(lowered.startswith(prefix) for prefix in JUNK_PREFIXES)
    ):
        return None

    cleaned_tokens = []
    for token in s.split():
        if re.fullmatch(r"(?:[A-Z]\.){2,}[A-Z]?\.?", token):
            cleaned_tokens.append(token)
            continue

        if token in INITIALISM_TOKENS:
            cleaned_tokens.append(token)
            continue

        if token.upper() in FACILITY_ACRONYMS:
            cleaned_tokens.append(token.upper())
            continue

        if token.isdigit():
            cleaned_tokens.append(token)
            continue

        if "/" in token:
            cleaned_tokens.append(
                "/".join(
                    part.upper() if part.upper() in FACILITY_ACRONYMS else part.capitalize()
                    for part in token.split("/")
                )
            )
            continue

        if "-" in token:
            cleaned_tokens.append(
                "-".join(
                    part.upper() if part.upper() in FACILITY_ACRONYMS else part.capitalize()
                    for part in token.split("-")
                )
            )
            continue

        if "'" in token:
            first, *rest = token.split("'")
            rebuilt = first.capitalize()
            if rest:
                rebuilt += "'" + "'".join(piece.capitalize() for piece in rest)
            cleaned_tokens.append(rebuilt)
            continue

        if token.isupper() and len(token) <= 4:
            cleaned_tokens.append(token)
            continue

        cleaned_tokens.append(token.capitalize())

    s = " ".join(cleaned_tokens).strip()
    s = s.replace("Women S", "Women's").replace("Men S", "Men's")
    s = s.replace("Asg", "ASG").replace("Esi", "ESI").replace("Srl", "SRL")
    s = s.replace("Sms", "SMS").replace("Kd", "KD").replace("Hcg", "HCG")
    s = s.replace("Echs", "ECHS").replace("Ivf", "IVF").replace("Mri", "MRI")
    s = s.replace("Ct", "CT").replace("Pet", "PET").replace("Icu", "ICU")
    s = s.replace("Nicu", "NICU").replace("Opd", "OPD").replace("Ent", "ENT")
    s = s.replace("Nabh", "NABH").replace("Aiims", "AIIMS").replace("Bms", "BMS")
    s = s.replace("24x7", "24x7").replace("3d", "3D")
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


standardize_facility_name_udf = F.udf(standardize_facility_name, T.StringType())


def nullify_empty(col):
    return F.when(F.trim(col) == "", F.lit(None)).otherwise(col)


def clean_text(col):
    cleaned = F.regexp_replace(
        F.regexp_replace(F.trim(F.regexp_replace(col, r"[\x00-\x1f\x7f]", " ")), r"\s+", " "),
        r"\s+",
        " ",
    )
    return F.when(col.isNull(), F.lit(None)).otherwise(nullify_empty(cleaned))


df = spark.table(source_fqn)

silver_df = (
    df
    .withColumn("Name_Standardized", standardize_facility_name_udf(F.col("name")))
    .withColumn("address_city", F.when(F.col("address_city").isNull(), F.lit(None)).otherwise(
        F.initcap(F.regexp_replace(F.regexp_replace(F.trim(F.regexp_replace(F.col("address_city"), r"[\x00-\x1f\x7f]", " ")), r"\d+", ""), r"\s+", " "))
    ))
    .withColumn("address_stateOrRegion", F.when(F.col("address_stateOrRegion").isNull(), F.lit(None)).otherwise(
        F.initcap(F.regexp_replace(F.regexp_replace(F.trim(F.regexp_replace(F.col("address_stateOrRegion"), r"[\x00-\x1f\x7f]", " ")), r"\d+", ""), r"\s+", " "))
    ))
    .withColumn("address_zipOrPostcode", clean_text(F.col("address_zipOrPostcode")))
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
          COUNT_IF(name <> Name_Standardized) AS changed_rows,
          COUNT_IF(Name_Standardized IS NULL) AS null_standardized
        FROM {target_fqn}
        """
    )
)

# COMMAND ----------

# Spot-check the cleaned names after load.
display(
    spark.sql(
        f"""
        SELECT name, Name_Standardized
        FROM {target_fqn}
        WHERE name IS NOT NULL AND Name_Standardized IS NOT NULL AND name <> Name_Standardized
        LIMIT 20
        """
    )
)
