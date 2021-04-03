name := "eVote-spark"

version := "1.0.0"

scalaVersion := "2.12.13"

// https://mvnrepository.com/artifact/org.apache.spark/spark-core
libraryDependencies += "org.apache.spark" %% "spark-core" % "3.1.1"
// https://mvnrepository.com/artifact/org.apache.spark/spark-sql
libraryDependencies += "org.apache.spark" %% "spark-sql" % "3.1.1"
libraryDependencies +=  "org.scalaj" %% "scalaj-http" % "2.4.2"
//// https://mvnrepository.com/artifact/com.typesafe.akka/akka-http
//libraryDependencies += "com.typesafe.akka" %% "akka-http" % "10.1.14"
//// https://mvnrepository.com/artifact/com.typesafe.akka/akka-actor
//libraryDependencies += "com.typesafe.akka" %% "akka-actor" % "2.6.13"
//// https://mvnrepository.com/artifact/com.typesafe.akka/akka-actor-typed
//libraryDependencies += "com.typesafe.akka" %% "akka-actor-typed" % "2.6.13"
