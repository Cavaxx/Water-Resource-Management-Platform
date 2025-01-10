import os
import logging
import sys
import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import FloatType
from pyspark.sql.functions import col, sum as spark_sum, avg as spark_avg



# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("SPEI_Calculator")

def initialize_spark():
    """
    Initialize and return a Spark session configured for MongoDB read/write.
    """
    spark = (
        SparkSession.builder
        .appName("SPEI_Calculation")
        .config("spark.driver.extraClassPath", "/opt/bitnami/spark/jars/*")
        .config("spark.executor.extraClassPath", "/opt/bitnami/spark/jars/*")
        .getOrCreate()
    )
    return spark

def load_data(spark, mongo_uri, db_name, collection_names):
    """
    Load weather data from multiple MongoDB collections into a single DataFrame.
    """
    required_cols = ["city", "rain", "temp_min", "temp_max", "timestamp"]

    dataframes = []
    for coll_name in collection_names:
        logger.info(f"Loading data from collection: {coll_name}")
        df = (
            spark.read.format("mongodb")
            .option("spark.mongodb.read.connection.uri", mongo_uri)
            .option("spark.mongodb.read.database", db_name)
            .option("spark.mongodb.read.collection", coll_name)
            .load()
        )
        for col_name in required_cols:
            if col_name not in df.columns:
                df = df.withColumn(col_name, F.lit(None).cast(FloatType()))
        df = df.select(*required_cols)
        dataframes.append(df)

    if not dataframes:
        raise ValueError("No collections to load. Check INPUT_COLLECTIONS environment variable.")

    unified_df = dataframes[0]
    for df in dataframes[1:]:
        unified_df = unified_df.union(df)

    return unified_df

def assign_synthetic_timestamps(df, start_date, frequency):
    """
    Assign synthetic timestamps to the DataFrame based on the specified frequency.
    """
    pandas_df = df.toPandas()
    num_records = len(pandas_df)

    start_date = pd.Timestamp(start_date)
    max_timestamp = pd.Timestamp.max
    frequency = pd.DateOffset(months=1)

    # Calculate the maximum number of records that can safely fit
    months_between = (max_timestamp.year - start_date.year) * 12 + (max_timestamp.month - start_date.month)
    max_safe_records = months_between

    if num_records > max_safe_records:
        logger.warning(f"Reducing num_records to {max_safe_records} to avoid overflow.")
        pandas_df = pandas_df.iloc[:max_safe_records]
        num_records = max_safe_records

    synthetic_dates = [start_date + i * frequency for i in range(num_records)]
    pandas_df["timestamp"] = synthetic_dates

    # Handle edge cases if the DataFrame is empty
    if pandas_df.empty:
        logger.warning("DataFrame is empty after timestamp assignment.")
        return spark.createDataFrame(pandas_df)

    return spark.createDataFrame(pandas_df)


def calculate_thornthwaite_pet(avg_temp, latitude):
    """
    Calculate PET using the Thornthwaite method.
    """
    if avg_temp <= 0:
        return 0.0

    I = (avg_temp / 5.0) ** 1.514
    a = 6.75e-7 * I**3 - 7.71e-5 * I**2 + 1.792e-2 * I + 0.49239
    PET = 16 * (10 * avg_temp / I) ** a
    return PET

def calculate_spei(drought_series, scale=3):
    """
    Calculate SPEI (Standardized Precipitation-Evapotranspiration Index).
    """
    drought_series = drought_series.dropna()
    mu, std = stats.norm.fit(drought_series)
    spei = (drought_series - mu) / std
    return pd.Series(index=drought_series.index, data=spei)

def calculate_pet_and_spei(df):
    """
    Calculate PET and SPEI for each city in the DataFrame.
    """
    required_cols = {"rain", "temp_min", "temp_max", "timestamp", "city"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")

    df = df.withColumn(
        "precipitation",
        F.coalesce(col("rain").getField("1h"), F.lit(0.0)).cast(FloatType())
    ).na.fill({"precipitation": 0.0})

    df = df.withColumn("month", F.month("timestamp"))

    aggregated_df = df.groupBy("city", "month").agg(
        spark_avg("temp_min").alias("avg_temp_min"),
        spark_avg("temp_max").alias("avg_temp_max"),
        spark_sum("precipitation").alias("total_precipitation")
    )

    pandas_df = aggregated_df.toPandas()
    if pandas_df.empty:
        logger.warning("No data to process after aggregation.")
        return pandas_df

    pandas_df["avg_temp"] = (pandas_df["avg_temp_min"] + pandas_df["avg_temp_max"]) / 2

    city_latitudes = {
        "Trento": 46.0679,
        "Rovereto": 45.8896,
        "Pergine Valsugana": 46.065,
        "Arco": 45.9177,
        "Riva del Garda": 45.8858,
         "Mori": 45.8711,
        "Mezzolombardo": 46.2125,
        "Aalen": 48.8377,
        "Lavis": 46.1815,
        "Borgo Valsugana": 46.0500
    }

    pandas_df["latitude"] = pandas_df["city"].map(city_latitudes)

    if pandas_df["latitude"].isnull().any():
        missing_cities = pandas_df[pandas_df["latitude"].isnull()]["city"].unique()
        raise ValueError(f"Missing latitude data for cities: {missing_cities}")

    pet_list = []
    for city, group in pandas_df.groupby("city"):
        I = (group["avg_temp"] / 5.0) ** 1.514
        a = 6.75e-7 * I.sum()**3 - 7.71e-5 * I.sum()**2 + 1.792e-2 * I.sum() + 0.49239
        group["pet"] = 16 * (10 * group["avg_temp"] / I.sum()) ** a
        group["drought"] = group["total_precipitation"] - group["pet"]
        group = group.sort_values("month")
        group["spei"] = calculate_spei(group["drought"], scale=3)
        pet_list.append(group)

    return pd.concat(pet_list)

def save_results_to_mongo(spark, pandas_df, mongo_uri, db_name, collection_name):
    """
    Write SPEI results back to MongoDB.
    """
    if pandas_df.empty:
        logger.info("SPEI DataFrame is empty, skipping write to MongoDB.")
        return

    spei_df = spark.createDataFrame(pandas_df)
    spei_df.write.format("mongodb").option(
        "spark.mongodb.write.connection.uri", mongo_uri
    ).option("spark.mongodb.write.database", db_name).option(
        "spark.mongodb.write.collection", collection_name
    ).mode("append").save()

if __name__ == "__main__":
    spark = initialize_spark()
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
    DB_NAME = os.getenv("DB_NAME", "water_management")
    raw_collections = os.getenv("INPUT_COLLECTIONS", "weather_data,synthetic_weather_data")
    INPUT_COLLECTIONS = raw_collections.split(",")
    OUTPUT_COLLECTION = os.getenv("OUTPUT_COLLECTION", "SPEI_PET")

    try:
        weather_df = load_data(spark, MONGO_URI, DB_NAME, INPUT_COLLECTIONS)
        START_DATE = "2020-01-01"
        FREQUENCY = "ME"
        weather_df = assign_synthetic_timestamps(weather_df, START_DATE, FREQUENCY)
        spei_results = calculate_pet_and_spei(weather_df)
        save_results_to_mongo(spark, spei_results, MONGO_URI, DB_NAME, OUTPUT_COLLECTION)
        logger.info(f"SPEI calculation complete. Results stored in MongoDB -> {OUTPUT_COLLECTION}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        spark.stop()

