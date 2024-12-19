from collections import defaultdict
from classes.redisManipulator import redisMani
from classes.pymongo_utils import PyMongoUtils
import redis
import json

class wordManipulator:
    def findMostCommonWord(collection):
        most_common = collection.find_one(sort=[("count", -1)]) #sort gunakan pymongo function
        print("Most common word:")
        print(json.dumps(most_common, indent=4, default=str)) #format

    def findMostLeastWord(collection):
        least_common = collection.find_one(sort=[("count", 1)]) #sort gunakan pymongo function
        print("Least common word:")
        print(json.dumps(least_common, indent=4, default=str)) #format

    def segmentWordPOS(uri, collection):
        #Refresher
        redisM = redisMani()
        redisM.flushRedis()
        pymongo_utils = PyMongoUtils(uri)
        pymongo_utils.insertAllWordsIntoRedis(collection)

        
        r = redis.StrictRedis(host='localhost', port=6379, db=0) #konek ke redis
        posFrequency = defaultdict(int) #declara satu dictionary bagi save the frequency of each pos
        keys = r.keys('word:*') #key dlm format word:baik macam tu
        
        for key in keys:
            wordData = r.hgetall(key) #dapatkan every key 
            
            if wordData:
                wordData = {k.decode('utf-8'): v.decode('utf-8') for k, v in wordData.items()} 
                posValue = wordData.get('pos') #dapatkan value pos
                if posValue:
                    posFrequency[posValue] += 1
        
        print("Word Frequency by Part of Speech:")
        for pos, freq in posFrequency.items():
            print(f"{pos}: {freq}")

    def findSentimentProportion(self, uri, collection):
        #Refresher
        redisM = redisMani()
        redisM.flushRedis()
        pymongo_utils = PyMongoUtils(uri)
        pymongo_utils.insertAllWordsIntoRedis(collection)
        
        r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
        sentimentCount = {"positive": 0, "negative": 0, "neutral": 0}
        totalWords = 0
        
        for key in r.scan_iter("word:*"):
            sentiment = r.hget(key, "sentiment")
            if sentiment in sentimentCount: 
                sentimentCount[sentiment] += 1
                totalWords += 1
        
        sentimentProportions = {k: v / totalWords for k, v in sentimentCount.items()}

        print("Sentiment Counts and Proportions:")
        for sentiment, count in sentimentCount.items():
            proportion = sentimentProportions[sentiment] * 100  # Convert to percentage
            print(f"{sentiment.capitalize()}: {count} words ({proportion:.2f}%)")

    def findWordSentiment(self, word, uri, collection):
        #Refresher
        redisM = redisMani()
        redisM.flushRedis()
        pymongo_utils = PyMongoUtils(uri)
        pymongo_utils.insertAllWordsIntoRedis(collection)
    
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        key = f"word:{word}"
        
        if r.exists(key):
            sentimentData = r.hgetall(key)
            print(f"Word '{word}' found in Redis with sentiment data:")

            #Show sentimenttt
            sentiment = sentimentData.get('sentiment', 'N/A')
            sentiment_scores = sentimentData.get('sentiment_scores', 'N/A')
            print(f"Sentiment: {sentiment}")
            print(f"Sentiment Scores: {sentiment_scores}")
            wordManipulator.findWordMeaning(wordManipulator, word, uri, collection) #the determinator is standy for further improvement if wanted
        else:
            print(f"Word '{word}' not found in Redis.")
            scenario = 'newWord'
            word_data = wordManipulator.wordInput(wordManipulator, word, scenario, uri)

    def findWordMeaning(self, word, uri, collection):
        #Refresher
        redisM = redisMani()
        redisM.flushRedis()
        pymongo_utils = PyMongoUtils(uri)
        pymongo_utils.insertAllWordsIntoRedis(collection)

        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        key = f"word:{word}"
        
        if r.exists(key):       
            sentimentData = r.hgetall(key)
            #Extra information
            print("======================================")
            print("\n\n\n\n")
            print("======================================")
            print(f"Here is some information about '{word}'")

            for field, value in sentimentData.items():
                print(f"\n{field.capitalize()}: {value}")
                
            return "N"
        else:
            return "Y"

    def wordInput(self, word, scenario, uri):
        if scenario == 'newWord' :
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            key = f"word:{word}"
            
            if not r.exists(key):  
                word = word
                count = 1
                meaning = input(f"\nEnter meaning for the word '{word}': ").strip()
                POS = input(f"\nEnter part of speech (noun, verb, etc.) for the word '{word}': ").strip()
                sentiment = input(f"\nEnter sentiment (positive/negative/neutral) for the word '{word}': ").strip()
                sentimentScore = float(input(f"\nEnter sentiment score (0.5 to 1) for the word '{word}': ").strip())
                synonyms = input(f"\nEnter synonyms for the word, put - if no. '{word}': ").strip()
                antonyms = input(f"\nEnter antonyms for the word, put - if no. '{word}': ").strip()
                hypernyms = input(f"\nEnter hypernyms for the word, put - if no.  '{word}': ").strip()
                meronyms = input(f"\nEnter meronyms for the word, put - if no.  '{word}': ").strip()
      
                word_data = {
                    "word": word,
                    "count": count,
                    "meaning": meaning,
                    "pos": POS,
                    "sentiment": sentiment,
                    "sentiment_scores": sentimentScore,
                    "synonyms": synonyms,
                    "antonyms": antonyms,
                    "hypernyms": hypernyms,
                    "meronyms": meronyms,
                }
                redisMani.insertIntoRedisAndMongo(word, word_data, uri)
            else:
                print("Already existed.")

        if scenario == 'update' :
            word = word
            count = int(redisMani.getCountRedis(word))
            meaning = input(f"\nEnter meaning for the word '{word}': ").strip()
            POS = input(f"\nEnter part of speech (noun, verb, etc.) for the word '{word}': ").strip()
            sentiment = input(f"\nEnter sentiment (positive/negative/neutral) for the word '{word}': ").strip()
            sentimentScore = float(input(f"\nEnter sentiment score (0.5 to 1) for the word '{word}': ").strip())
            synonyms = input(f"\nEnter synonyms for the word, put - if no. '{word}': ").strip()
            antonyms = input(f"\nEnter antonyms for the word, put - if no. '{word}': ").strip()
            hypernyms = input(f"\nEnter hypernyms for the word, put - if no.  '{word}': ").strip()
            meronyms = input(f"\nEnter meronyms for the word, put - if no.  '{word}': ").strip()
  
            word_data = {
                "word": word,
                "count": count,
                "meaning": meaning,
                "pos": POS,
                "sentiment": sentiment,
                "sentiment_scores": sentimentScore,
                "synonyms": synonyms,
                "antonyms": antonyms,
                "hypernyms": hypernyms,
                "meronyms": meronyms,
            }
            redisMani.updateIntoRedisAndMongo(word, word_data, uri)


    def wordAccuracyTest(self, word, uri, collection):
        exitOrNot = wordManipulator.findWordMeaning(wordManipulator, word, uri, collection)
        if exitOrNot == "N":
            determinator = input(f"\nIs the information about '{word}' correct? (Y/N): ")
            if determinator == 'Y' or determinator == 'y':
                print("Alright! Thank you!")
            elif determinator == 'N' or determinator == 'n':
                determinatorTwo = input("I see! You could remodify the information if you want, do you like to proceed to modify? (Y/N):")
                if determinatorTwo == 'Y' or determinatorTwo == 'y':
                    scenario = 'update'
                    wordManipulator.wordInput(wordManipulator, word, scenario, uri)
                elif determinatorTwo == 'N' or determinatorTwo == 'N':
                    print("Alright! Thank you!")
                else: 
                    print("Invalid Input!")
                    
            else:
                print("Invalid Input!")
        elif exitOrNot == "Y": 
            print(f"Word '{word}' not found in Redis.")
            scenario = 'newWord'
            word_data = wordManipulator.wordInput(wordManipulator, word, scenario, uri)



        
