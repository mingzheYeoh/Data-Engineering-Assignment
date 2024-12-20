#Author: Lim Wai Ming

from pymongo import MongoClient
import redis

class PyMongoUtils:
    
    def __init__(self, uri):
        self.uri = uri    

    def get_database(self, database_name):
        client = MongoClient(self.uri)
        return client[database_name]
    
    def insertIntoMongo(self, df, collection):
        #df = df.limit(df.count() - 1) #dw the header
        records = []

        #error handling and changing count value to integer type (they are string type in original df)
        for row in df.collect():
            if isinstance(row['count'], (str, int, float)) and row['count'] != 'count':  
                try:
                    count_value = int(row['count']) if row['count'] is not None else 0 
                except ValueError:
                    print(f"Invalid count value: {row['count']}")  
                    count_value = 0 
        
                record = {
                    "word": row['word'],
                    "count": count_value,  
                    "annotation": {
                        "sentiment": row['sentiment'] if "sentiment" in row else "-",
                        "sentiment_scores": row['sentiment_score'] if "sentiment_score" in row else 0.0,
                        "synonyms": row['synonym'] if "synonym" in row else "-",
                        "antonyms": row['antonyms'] if "antonyms" in row else "-",
                        "hypernyms": row['hypernyms'] if "hypernyms" in row else "-",
                        "meronyms": row['meronyms'] if "meronyms" in row else "-",
                    },
                    "meaning": row['meaning'] if "meaning" in row else "-",
                    "pos": row['POS'] if "POS" in row else "-",
                }
                records.append(record)
        
        if records:
            result = collection.insert_many(records)
            print(f"Inserted {len(result.inserted_ids)} documents into MongoDB.")
        else:
            print("No records to insert.")

    def insertAllWordsIntoRedis(self, mongo_collection):
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
        for document in mongo_collection.find():
            word = document.get("word")
            
            if word: 
                redis_key = f"word:{word}"
                
                data = {
                    "word": document.get("word", "-"),
                    "count": document.get("count", 0),
                    "meaning": document.get("meaning", "-"),
                    "pos": document.get("pos", "-"),
                    "sentiment": document.get("annotation", {}).get("sentiment", "-"),
                    "sentiment_scores": document.get("annotation", {}).get("sentiment_scores", 0.0),
                    "synonyms": document.get("annotation", {}).get("synonyms", "-"),
                    "antonyms": document.get("annotation", {}).get("antonyms", "-"),
                    "hypernyms": document.get("annotation", {}).get("hypernyms", "-"),
                    "meronyms": document.get("annotation", {}).get("meronyms", "-")
                }
    
                r.hmset(redis_key, data)
            else:
                print("Skipping document without a valid word field.")
        
        print("Insertion into Redis completed.")


    def insertIntoMongoDB(self, data):
        database_name = "lexicon"
        collection_name = "annotated_words"  
        dbMani = self.get_database(database_name)
        collection = dbMani[collection_name]
    
        record = {
            "word": data['word'],
            "count": data['count'] if 'count' in data else 0,
            "annotation": {
                "sentiment": data['sentiment'] if "sentiment" in data else "-",
                "sentiment_scores": data['sentiment_scores'] if "sentiment_scores" in data else 0.0,
                "synonyms": data['synonyms'] if "synonyms" in data else "-",
                "antonyms": data['antonyms'] if "antonyms" in data else "-",
                "hypernyms": data['hypernyms'] if "hypernyms" in data else "-",
                "meronyms": data['meronyms'] if "meronyms" in data else "-",
            },
            "meaning": data['meaning'] if "meaning" in data else "-",
            "pos": data['pos'] if "pos" in data else "-",
        }
    
        collection.insert_one(record)
        print(f"\nInserted word '{record['word']}' into MongoDB.")


    def updateIntoMongoDB(self, data):
        database_name = "lexicon"
        collection_name = "annotated_words"
        dbMani = self.get_database(database_name)
        collection = dbMani[collection_name]
    
        record = {
            "word": data['word'],
            "count": data['count'] if 'count' in data else 0,
            "annotation": {
                "sentiment": data['sentiment'] if "sentiment" in data else "-",
                "sentiment_scores": data['sentiment_scores'] if "sentiment_scores" in data else 0.0,
                "synonyms": data['synonyms'] if "synonyms" in data else "-",
                "antonyms": data['antonyms'] if "antonyms" in data else "-",
                "hypernyms": data['hypernyms'] if "hypernyms" in data else "-",
                "meronyms": data['meronyms'] if "meronyms" in data else "-",
            },
            "meaning": data['meaning'] if "meaning" in data else "-",
            "pos": data['pos'] if "pos" in data else "-",
        }
    
        collection.update_one(
            {"word": record["word"]}, 
            {"$set": record},          
            upsert=True                
        )

        print(f"\nUpdated word '{record['word']}' into MongoDB.")
    


