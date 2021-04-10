#! /bin/bash

cd eVote-spark && sbt clean package
gsutil cp target/scala-2.12/evote-spark_2.12-1.0.0.jar gs://evote-cdn/jar/
cd ..

echo "Done!"
