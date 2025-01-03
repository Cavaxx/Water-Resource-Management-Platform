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
    Initialize and return a Spark session configured for MongoDB read/write
    (requires the MongoDB Spark connector).
    """
    spark = (
        SparkSession.builder
        .appName("SPEI_Calculation")
        # .master(...)  # Typically you rely on --master in spark-submit OR spark cluster environment
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.1.3")

        .getOrCreate()
    )
    return spark


def load_data(spark, mongo_uri, db_name, collection_names):
    """
    Load weather data from multiple MongoDB collections into a single DataFrame.
    
    :param spark: SparkSession
    :param mongo_uri: Base Mongo URI, e.g., "mongodb://mongo:27017/"
    :param db_name: Database name, e.g. "weather_db"
    :param collection_names: List of collection names, e.g. ["weather_data", "synthetic_weather_data"]
    :return: A unified Spark DataFrame
    """
    dataframes = []
    for collection_name in collection_names:
        logger.info(f"Loading from collection: {collection_name}")
        df = (
            spark.read.format("mongo")
            .option("uri", f"{mongo_uri}{db_name}.{collection_name}")
            .load()
        )
        dataframes.append(df)

    if not dataframes:
        raise ValueError("No collections to load. Check INPUT_COLLECTIONS environment variable.")

    # Combine all dataframes
    unified_df = dataframes[0]
    for df in dataframes[1:]:
        unified_df = unified_df.union(df)

    return unified_df


def calculate_pet_and_spei(df):
    """
    Calculate PET (Potential Evapotranspiration) and SPEI (Standardized Precipitation-Evapotranspiration Index)
    for each city in the DataFrame.
    
    :param df: Spark DataFrame with columns at least: city, rain (precip), temp_min, temp_max
    :return: Pandas DataFrame containing city, total_precipitation, pet, spei, etc.
    """
    # Ensure required columns exist, fill missing precipitation
    if "rain" not in df.columns or "temp_min" not in df.columns or "temp_max" not in df.columns:
        raise ValueError("Missing required columns in DataFrame: need 'rain', 'temp_min', 'temp_max'.")

    df = df.withColumn("precipitation", col("rain").cast(FloatType()).na.fill(0.0))
    
    # Aggregate data by city
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

    # Simple placeholder for PET calculation
    pandas_df['avg_temp'] = (pandas_df['avg_temp_min'] + pandas_df['avg_temp_max']) / 2
    
    # For demonstration, hardcode lat=46.0 for all rows. Or load actual lat per city if needed.
    latitudes = [46.0] * len(pandas_df)

    pandas_df['pet'] = compute.pet_thornthwaite(
        pandas_df['avg_temp'].values,
        latitudes=latitudes
    )

    # Calculate simple "drought" = precipitation - PET
    pandas_df['drought'] = pandas_df['total_precipitation'] - pandas_df['pet']

    # SPEI with scale=3
    spei_values = compute.spei(pandas_df['drought'].values, scale=3)
    pandas_df['spei'] = spei_values

    return pandas_df


def save_results_to_mongo(spark, pandas_df, mongo_uri, db_name, collection_name):
    """
    Write the SPEI results back to MongoDB in a specified collection.
    :param spark: SparkSession
    :param pandas_df: Pandas DataFrame with the SPEI fields
    :param mongo_uri: e.g., "mongodb://mongo:27017/"
    :param db_name: e.g., "weather_db"
    :param collection_name: e.g., "SPEI_PET"
    """
    if pandas_df.empty:
        logger.info("SPEI DataFrame is empty, skipping write to MongoDB.")
        return

    spei_df = spark.createDataFrame(pandas_df)
    spei_df.write.format("mongo") \
        .option("uri", f"{mongo_uri}{db_name}.{collection_name}") \
        .mode("append") \
        .save()
    logger.info(f"Saved SPEI results to MongoDB -> {db_name}.{collection_name}")


if __name__ == "__main__":
    spark = initialize_spark()

    # Load environment variables
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
    DB_NAME = os.getenv("DB_NAME", "water_management")
    INPUT_COLLECTIONS = os.getenv("INPUT_COLLECTIONS", "weather_data,synthetic_weather_data").split(",")
    OUTPUT_COLLECTION = os.getenv("OUTPUT_COLLECTION", "SPEI_PET")

    try:
        # 1. Load data
        weather_df = load_data(spark, MONGO_URI, DB_NAME, INPUT_COLLECTIONS)

        # 2. Calculate PET and SPEI
        spei_results = calculate_pet_and_spei(weather_df)

        # 3. Write results
        save_results_to_mongo(spark, spei_results, MONGO_URI, DB_NAME, OUTPUT_COLLECTION)

        logger.info(
            "SPEI calculation complete. Results stored in MongoDB collection '{}.{}'".format(
                DB_NAME, OUTPUT_COLLECTION
            )
        )
    except Exception as e:
        logger.error(f"Error in SPEI calculation flow: {e}", exc_info=True)
        sys.exit(1)
    finally:
        spark.stop()
