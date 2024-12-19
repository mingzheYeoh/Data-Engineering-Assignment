from pyspark.sql import SparkSession

class sparkBuilder:

    def sparkSessionBuilder(self, name):
        spark = SparkSession.builder.appName(name).getOrCreate()
        return spark

    def sparkStopSession(self, spark):
        spark.stop()