from classes.LexiconAnnotater import lexiconAnnotater
from classes.LexiconCreator import lexiconRawDataCollector
from classes.pymongo_utils import PyMongoUtils
from classes.SparkBuilder import sparkBuilder
from classes.redisManipulator import redisMani
from pyspark.sql import SparkSession
from datetime import datetime



class csvUpdateUtils:
    def compareToUpdateCSV(self, spark, csvDate, refresherName, uri, database, collection_name):
        #Classes
        lexicon = lexiconAnnotater()
        sB = sparkBuilder()
        redisM = redisMani()
        
        mongoUtils = PyMongoUtils(uri)
        dbMani = mongoUtils.get_database(database)
        collection = dbMani[collection_name]

        #New Records If Exist
        path = f"storageCleanedCSV/cleaned_words_{csvDate}_{refresherName}.csv"
        dfNew = lexicon.importCSVintoDF(spark, path)

        #Existing Records
        #Refresh the redis to make sure everything up to date.
        redisM.flushRedis()
        mongoUtils.insertAllWordsIntoRedis(collection)
        dfOld = spark.createDataFrame(redisM.redisGetAllData())
        
        #Now Compare the word
        dfNewWords = dfNew.select("word")
        dfOldWords = dfOld.select("word")
        dfNewWordsOnly = dfNewWords.subtract(dfOldWords)
        dfNewWordsOnly.show()
        row_count = dfNew.count()
        print(f"Number of rows in DataFrame: {row_count}")

        return dfNewWordsOnly

    def exportUpdateCSV(self, df):
        #Classes
        lexicon = lexiconRawDataCollector()
        currentDateTime = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        refresherName = "LWM"
        output_path = f"storageContinuousUpdateCSV/updateCSVOf_{currentDateTime}_{refresherName}.csv"
        lexicon.exportToCSV(df, output_path)


    def importUpdatedCSVToMongo(self, spark, scenario, csvDateFileWanted, refresherName, uri, database, collection_name):
        #Classes
        lexicon = lexiconAnnotater()
        redisM = redisMani()
        
        mongoUtils = PyMongoUtils(uri)
        dbMani = mongoUtils.get_database(database)
        collection = dbMani[collection_name]

        #Refresh the redis to make sure everything up to date.
        redisM.flushRedis()
        mongoUtils.insertAllWordsIntoRedis(collection)
        
        if scenario == 1:
            input_path = f"storageLabeledUpdateCSV/labeled_updateCSVOf_{csvDateFileWanted}_by_{refresherName}.csv"
            df = lexicon.importCSVintoDF(spark, input_path)    
            mongoUtils.insertIntoMongo(df, collection)
            redisM.flushRedis()
            mongoUtils.insertAllWordsIntoRedis(collection)
        elif scenario == 2:
            input_path = f"storageContinuousUpdateCSV/updateCSVOf_{csvDateFileWanted}_{refresherName}.csv"
            df = lexicon.importCSVintoDF(spark, input_path)   
            mongoUtils.insertIntoMongo(df, collection)
            redisM.flushRedis()
            mongoUtils.insertAllWordsIntoRedis(collection)
        else:
            print("Invalid Input!")
            
            





