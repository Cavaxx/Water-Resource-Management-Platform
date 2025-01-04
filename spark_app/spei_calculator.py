import os
import logging
import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, avg as spark_avg
from pyspark.sql.types import FloatType
from climate_indices import compute
import pandas as pd

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
        # If you have JARs placed in /opt/bitnami/spark/jars, these lines
        # can help ensure the driver & executors see them. 
        .config("spark.driver.extraClassPath", "/opt/bitnami/spark/jars/*")
        .config("spark.executor.extraClassPath", "/opt/bitnami/spark/jars/*")
        .getOrCreate()
    )
    return spark


def load_data(spark, mongo_uri, db_name, collection_names):
    """
    Load weather data from multiple MongoDB collections into a single DataFrame,
    using the updated 10.x Mongo Spark Connector syntax.
    
    :param spark: SparkSession
    :param mongo_uri: Base Mongo URI, e.g. "mongodb://mongo:27017"
    :param db_name: e.g. "weather_db"
    :param collection_names: List of collection names, e.g. ["weather_data", "synthetic_weather_data"]
    :return: A unified Spark DataFrame
    """
    dataframes = []
    for coll_name in collection_names:
        logger.info(f"Loading from collection: {coll_name}")
        df = (
            spark.read.format("mongodb")
            # For 10.x connector, specify these keys:
            .option("spark.mongodb.read.connection.uri", mongo_uri)
            .option("spark.mongodb.read.database", db_name)
            .option("spark.mongodb.read.collection", coll_name)
            .load()
        )
        dataframes.append(df)

    if not dataframes:
        raise ValueError("No collections to load. Check INPUT_COLLECTIONS environment variable.")

    # Combine all dataframes via union
    unified_df = dataframes[0]
    for df in dataframes[1:]:
        unified_df = unified_df.union(df)

    return unified_df


def calculate_pet_and_spei(df):
    """
    Calculate PET (Potential Evapotranspiration) and SPEI (Standardized Precipitation-Evapotranspiration Index)
    for each city in the DataFrame.
    
    Requires columns: city, rain, temp_min, temp_max.
    """
    required_cols = {"rain", "temp_min", "temp_max"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")

    # Fill missing rain with 0.0
    df = df.withColumn("precipitation", col("rain").cast(FloatType()).na.fill(0.0))
    
    # Aggregate by city
    aggregated_df = df.groupBy("city").agg(
        spark_avg("temp_min").alias("avg_temp_min"),
        spark_avg("temp_max").alias("avg_temp_max"),
        spark_sum("precipitation").alias("total_precipitation")
    )

    # Convert to Pandas
    pandas_df = aggregated_df.toPandas()
    if pandas_df.empty:
        logger.warning("No data to process after aggregation.")
        return pandas_df

    # Simple placeholder for PET calculation (Thornthwaite)
    pandas_df["avg_temp"] = (pandas_df["avg_temp_min"] + pandas_df["avg_temp_max"]) / 2
    latitudes = [46.0] * len(pandas_df)
    pandas_df["pet"] = compute.pet_thornthwaite(
        pandas_df["avg_temp"].values,
        latitudes=latitudes
    )
    # Drought = Precip - PET
    pandas_df["drought"] = pandas_df["total_precipitation"] - pandas_df["pet"]

    # Compute SPEI with scale=3
    spei_values = compute.spei(pandas_df["drought"].values, scale=3)
    pandas_df["spei"] = spei_values

    return pandas_df


def save_results_to_mongo(spark, pandas_df, mongo_uri, db_name, collection_name):
    """
    Write the SPEI results back to MongoDB in a specified collection,
    using new 10.x style config keys for writing.
    """
    if pandas_df.empty:
        logger.info("SPEI DataFrame is empty, skipping write to MongoDB.")
        return

    spei_df = spark.createDataFrame(pandas_df)
    (
        spei_df.write.format("mongodb")
        .option("spark.mongodb.write.connection.uri", mongo_uri)
        .option("spark.mongodb.write.database", db_name)
        .option("spark.mongodb.write.collection", collection_name)
        .mode("append")
        .save()
    )
    logger.info(f"Saved SPEI results to MongoDB -> {db_name}.{collection_name}")


if __name__ == "__main__":
    spark = initialize_spark()

    # Load environment variables
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
    DB_NAME = os.getenv("DB_NAME", "water_management")
    raw_collections = os.getenv("INPUT_COLLECTIONS", "weather_data,synthetic_weather_data")
    INPUT_COLLECTIONS = raw_collections.split(",")
    OUTPUT_COLLECTION = os.getenv("OUTPUT_COLLECTION", "SPEI_PET")

    try:
        # 1. Load data from multiple collections
        weather_df = load_data(spark, MONGO_URI, DB_NAME, INPUT_COLLECTIONS)

        # 2. Calculate PET and SPEI
        spei_results = calculate_pet_and_spei(weather_df)

        # 3. Write results back to MongoDB
        save_results_to_mongo(spark, spei_results, MONGO_URI, DB_NAME, OUTPUT_COLLECTION)

        logger.info(
            f"SPEI calculation complete. Results stored in MongoDB collection '{DB_NAME}.{OUTPUT_COLLECTION}'"
        )
    except Exception as e:
        logger.error(f"Error in SPEI calculation flow: {e}", exc_info=True)
        sys.exit(1)
    finally:
        spark.stop()
