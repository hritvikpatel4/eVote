package com.evote.spark

import org.apache.spark.sql.{SaveMode, SparkSession}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types.DataTypes
import scala.sys.process._

object EvoteResults {
  def main(args: Array[String]): Unit = {
    if (args.length != 2) {
      throw new IllegalArgumentException(
        "2 Arguments required: <inputPath> <outputPath>"
      )
    }

    val inputPath = args(0)
    val outputPath = args(1)

    val spark = SparkSession
      .builder
      .master("local[*]")
      .appName("eVote Results")
      .getOrCreate()

    val sc = spark.sparkContext
    sc.setLogLevel("ERROR")

    val ignoreCols = Seq("level_number", "cluster_id", "batch_id", "prevHash")

    val inputDF = spark
      .read
      .option("header", "true")
      .csv(inputPath)
      .drop(ignoreCols: _*)

    val csvDF = inputDF.withColumn("temp", lit(0))

    val exprs = csvDF.columns.map(
      colname => sum(
        col(colname).cast(DataTypes.LongType)
      ).as(colname)
    )

    val resultDF = csvDF.groupBy("temp")
                        .agg(exprs.head, exprs.slice(1, exprs.length): _*)
                        .drop("temp")

    resultDF
      .repartition(1)
      .write
      .mode(SaveMode.Overwrite)
      .option("header", "true")
      .json(outputPath)

    val jobComplete = Seq("curl", "https://hritvikpatel.me/api/job/complete")
    jobComplete.!

//    Thread.sleep(10000)

    sc.stop()
    spark.stop()
  }
}
