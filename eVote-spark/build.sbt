name := "eVote-spark"

version := "1.0.0"

scalaVersion := "2.12.13"

// https://mvnrepository.com/artifact/org.apache.spark/spark-core
libraryDependencies += "org.apache.spark" %% "spark-core" % "3.1.1"
// https://mvnrepository.com/artifact/org.apache.spark/spark-sql
libraryDependencies += "org.apache.spark" %% "spark-sql" % "3.1.1"
libraryDependencies +=  "org.scalaj" %% "scalaj-http" % "2.4.2"
