package com.evote.spark

//import akka.actor.typed.ActorSystem
//import akka.actor.typed.scaladsl.Behaviors
//import akka.http.scaladsl.Http
//import akka.http.scaladsl.model._
import scalaj.http._
import org.apache.spark.sql.{SaveMode, SparkSession}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types.DataTypes

//import scala.concurrent.Future
//import scala.util.{Failure, Success}

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

    val response: HttpResponse[String] = Http("https://hritvikpatel.me/api/job/complete").asString
    println(s"${response.code} - ${response.body}")

//    implicit val system = ActorSystem(Behaviors.empty, "SingleRequest")
//    implicit val executionContext = system.executionContext

//    val responseFuture: Future[HttpResponse] = Http(system).singleRequest(HttpRequest(uri = "https://hritvikpatel.me/api/job/complete"))

//    responseFuture.onComplete {
//      case Success(res) => println(res)
//      case Failure(_) => sys.error("Error sending ack for job completion to webserver")
//    }

//    Thread.sleep(10000)

    sc.stop()
    spark.stop()
  }
}
