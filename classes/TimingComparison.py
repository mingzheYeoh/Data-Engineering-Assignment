import time
import json
from .Neo4jRedisLexiconManager import Neo4jRedisLexiconManager

class RetrievalTimeAnalyzer:
    def __init__(self, neo4j_redis_manager):
        self.manager = neo4j_redis_manager

    def retrieve_from_redis(self, word):
        """Retrieve data from Redis."""
        cache_key = f"lexicon:{word}"
        start_time = time.time()
        data = self.manager.redis.get(cache_key)
        end_time = time.time()

        if data:
            print(f"Data for '{word}' retrieved from Redis: {json.loads(data)}")
        else:
            print(f"No data found in Redis for '{word}'.")

        return json.loads(data) if data else None, end_time - start_time

    def retrieve_from_aura(self, word):
        """Retrieve data from Aura DB."""
        query = """
        MATCH (w:Word {name: $word})
        RETURN w.POS as part_of_speech,
               w.sentiment as sentiment,
               w.sentiment_score as sentiment_score,
               w.meaning as definition
        """
        params = {"word": word}
        start_time = time.time()
        result = self.manager.driver.session().run(query, params).single()
        end_time = time.time()

        if result:
            print(f"Data for '{word}' retrieved from Aura DB: {dict(result)}")
        else:
            print(f"No data for '{word}' found in Aura DB.")

        return dict(result) if result else None, end_time - start_time

    def compare_retrieval_times(self, words):
        """Retrieve data for all words first, then compare retrieval times."""
        if not isinstance(words, list):
            raise ValueError("Input should be a list of words.")
        
        print(f"Retrieving data for the words: {words}\n")

        # Step 1: Retrieve data for all words
        redis_total_time = 0
        aura_total_time = 0
        redis_data = {}
        aura_data = {}

        for word in words:
            print(f"Retrieving data for word: '{word}'...")
            redis_result, redis_time = self.retrieve_from_redis(word)
            aura_result, aura_time = self.retrieve_from_aura(word)
            
            # Store data and accumulate times
            redis_data[word] = redis_result
            aura_data[word] = aura_result
            redis_total_time += redis_time
            aura_total_time += aura_time

        # Step 2: Display results
        print("\nComparison of Retrieval Times:")
        for word in words:
            print(f"\n--- Word: '{word}' ---")
            print("Redis Data:", redis_data[word])
            print("Aura DB Data:", aura_data[word])

        print("\n--- Total Retrieval Times ---")
        print(f"Redis Total Time: {redis_total_time:.4f} seconds")
        print(f"Aura DB Total Time: {aura_total_time:.4f} seconds")

        if redis_total_time < aura_total_time:
            print("\nRedis was faster overall.")
        elif redis_total_time > aura_total_time:
            print("\nAura DB was faster overall.")
        else:
            print("\nBoth had equal total retrieval times.")
