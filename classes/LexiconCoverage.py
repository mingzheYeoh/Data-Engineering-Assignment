# Author: Yeoh Ming Zhe

import json

class LexiconSizeCoverageCalculator:
    def __init__(self, neo4j_redis_manager):
        """
        Initialize the LexiconSizeCoverageCalculator with a Neo4jRedisLexiconManager instance.
        :param neo4j_redis_manager: An instance of the Neo4jRedisLexiconManager class
        """
        self.manager = neo4j_redis_manager

    def calculate_word_coverage(self, words):
        """
        Calculate the percentage of words that exist in Redis or AuraDB.
        :param words: List of words to check
        :return: Percentage of words found in the lexicon
        """
        found_count = 0
        total_words = len(words)

        for word in words:
            if self.word_exists_in_redis(word) or self.word_exists_in_aura(word):
                found_count += 1
            else:
                print(f"Word '{word}' not found in either Redis or AuraDB.")

        coverage_percentage = (found_count / total_words) * 100
        print(f"Coverage Percentage: {coverage_percentage:.2f}%")
        return coverage_percentage

    def word_exists_in_redis(self, word):
        """Check if a word exists in Redis."""
        key = f"lexicon:{word}"
        return self.manager.redis.get(key) is not None

    def word_exists_in_aura(self, word):
        """Check if a word exists in AuraDB."""
        with self.manager.driver.session() as session:
            query = "MATCH (w:Word {name: $word}) RETURN w"
            result = session.run(query, word=word).single()
            return result is not None

    def calculate_lexicon_size(self):
        """
        Calculate the total lexicon size by counting unique words in Redis and AuraDB.
        :return: Total lexicon size
        """
        redis_size = len(self.manager.redis.keys("lexicon:*"))
        print(f"Total words in Redis: {redis_size}")

        with self.manager.driver.session() as session:
            query = "MATCH (w:Word) RETURN count(w) AS total_words"
            result = session.run(query).single()
            aura_size = result["total_words"]
        print(f"Total words in AuraDB: {aura_size}")