# Author: Lim Wai Ming

from transformers import pipeline
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType, FloatType

class lexiconAnnotater:
    
    def importCSVintoDF(self, spark, path_name):
        csv_file_path = path_name
        df = spark.read.csv(csv_file_path, header=True, inferSchema=True)
        df.show()
        df.printSchema()
        return df

    def getWordValueFromCSV(self, df):
        words = df.select("word").rdd.flatMap(lambda x: x).collect()
        return words
           
    def sentimentLabeling(self, df, output_path):
        sentiment_analysis = pipeline("sentiment-analysis", model="malaysia-ai/deberta-v3-xsmall-malay-sentiment")
        
        wordAndCount = df.select("word", "count").collect()
        
        results = []
        for row in wordAndCount:
            word = row["word"]
            count = row["count"]

            
            sentiment = sentiment_analysis(word)[0]
            label = sentiment["label"]
            score = sentiment["score"]

            #Make it neutral
            if 0.3 < score < 0.7:
                label = "neutral"
                score = 0.5

                
            results.append((word, count, label, score))
        
        result_df = df.sparkSession.createDataFrame(results, ["word", "count", "sentiment", "sentiment_score"])
        result_df.show(truncate=False)
        result_df.coalesce(1).write.csv(output_path, header=True, mode="overwrite")
        print(f"Cleaned words with frequencies saved to {output_path}")


    def sentimentAnnotation(self, spark, fileName, csvDateFileWanted, refresherName):
        if fileName == "storageCleanedCSV": 
            input_path = f"{fileName}/cleaned_words_{csvDateFileWanted}_{refresherName}.csv"
            df = self.importCSVintoDF(spark, input_path)    
            output_path = f"storageLabeledCleanedCSV/labeled_cleanedCSVOf_{csvDateFileWanted}_by_{refresherName}.csv"
            self.sentimentLabeling(df, output_path)
            
        elif fileName == "storageContinuousUpdateCSV":
            input_path = f"{fileName}/updateCSVOf_{csvDateFileWanted}_{refresherName}.csv"
            df = self.importCSVintoDF(spark, input_path)    
            output_path = f"storageLabeledUpdateCSV/labeled_updateCSVOf_{csvDateFileWanted}_by_{refresherName}.csv"
            self.sentimentLabeling(df, output_path)
            
        else:
            print(f"Invalid Input! No predetermiend location for {fileName}")

    


