# Author: Yeoh Ming Zhe, Wong Shu Han
# Created At: 11.12.24

import csv
import os
import pprint
import redis
import json
from neo4j import GraphDatabase
from tqdm import tqdm
from colorama import Fore, Style

class Neo4jRedisLexiconManager:
    def __init__(self, uri, username, password, redis_host='localhost', redis_port=6379, redis_db=0):
        """Initialize the connection to the Neo4j, Redis and set OpenAI API Key"""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.redis = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def close(self):
        """Close the connection to Neo4j and Redis."""
        if self.driver:
            self.driver.close()
        if self.redis:
            self.redis.close()

    def sync_aura_to_redis(self):
        """Sync all existing keys and data from Aura DB to Redis with a colorful progress bar."""
        with self.driver.session() as session:
            result = session.run("MATCH (w:Word) RETURN w")
            records = list(result)
            total_records = len(records)

            if total_records == 0:
                print("No data found in Aura DB to sync.")
                return

            print("Synchronizing Aura DB data to Redis...")

            for _ in tqdm(records, desc="Syncing", unit="record", ncols=80, colour='blue'):
                # Extract node properties using dict()
                word = _["w"]  # This gets the Node object
                word_properties = dict(word)  # Convert node to a dictionary
                word_name = word_properties.get("name")  # Get the 'name' property

                if word_name:
                    # Serialize the node properties into a JSON string for Redis
                    self.redis.set(f"lexicon:{word_name}", json.dumps(word_properties))

            print(f"{Fore.GREEN}Synchronization complete. Total records synced: {total_records}{Style.RESET_ALL}")
    
    def verify_data_in_redis(self, word):
        """Check if a specific word's data exists in Redis."""
        key = f"lexicon:{word}"
        data = self.redis.get(key)
        if data:
            print(f"Data for '{word}' exists in Redis:")
            print(json.loads(data))  # Deserialize and display the JSON data
        else:
            print(f"No data for '{word}' found in Redis.")
            
    def validate_existence(self, word):
        """Check if a word node exists in Redis or Aura DB."""
        if self.redis.get(word):
            return True

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (w:Word {name: $word})
                RETURN w
                """,
                word=word
            ).single()
            return result is not None

    def create_word_node(self, word, pos=None, sentiment=None, sentiment_score=None, meaning=None):
        """Create a word node in both Redis and Aura DB if it does not already exist."""
        if self.validate_existence(word):
            print(f"Word '{word}' already exists. Creation aborted.")
            return

        word_data = {
            "name": word,
            "POS": pos,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "meaning": meaning,
        }

        # Write to Redis
        self.redis.set(f"lexicon:{word}", json.dumps(word_data))

        # Write to Aura DB
        with self.driver.session() as session:
            session.run(
                """
                MERGE (w:Word {name: $word})
                SET w.POS = $pos, w.sentiment = $sentiment,
                    w.sentiment_score = $sentiment_score,
                    w.meaning = $meaning
                """,
                word=word, pos=pos, sentiment=sentiment,
                sentiment_score=sentiment_score, meaning=meaning
            )

    def create_nodes_with_relationship(self, word1, word1_properties, word2, word2_properties, relationship):
        """Create two word nodes and a relationship between them in Redis and Aura DB."""

        # Check existence of word1 and word2
        if self.validate_existence(word1):
            print(f"Word '{word1}' already exists. Overwriting properties.")

        if self.validate_existence(word2):
            print(f"Word '{word2}' already exists. Overwriting properties.")

        # Word1 data
        word1_data = {"name": word1, **word1_properties}
        self.redis.set(f"lexicon:{word1}", json.dumps(word1_data))
        print(f"Word '{word1}' data stored in Redis with key 'lexicon:{word1}'")

        # Word2 data
        word2_data = {"name": word2, **word2_properties}
        self.redis.set(f"lexicon:{word2}", json.dumps(word2_data))
        print(f"Word '{word2}' data stored in Redis with key 'lexicon:{word2}'")

        # Write nodes and relationships to Aura DB
        with self.driver.session() as session:
            session.run(
                """
                MERGE (w1:Word {name: $word1})
                SET w1 += $word1_properties
                MERGE (w2:Word {name: $word2})
                SET w2 += $word2_properties
                MERGE (w1)-[r:`""" + relationship + """`]->(w2)
                RETURN w1, r, w2
                """,
                word1=word1,
                word1_properties=word1_properties,
                word2=word2,
                word2_properties=word2_properties
            )

        print(f"Nodes '{word1}' and '{word2}' with relationship '{relationship}' created successfully!")

    def update_node_or_relationship(self, word, properties=None, relationship=None, related_word=None):
        """Update a node's properties or create/update a relationship in Redis and Aura DB."""
        if not self.validate_existence(word):
            print(f"Word '{word}' does not exist. Update aborted.")
            return
    
        if properties:
            # Update properties in Redis
            key = f"lexicon:{word}"
            existing_data = self.redis.get(key)
            if existing_data:
                existing_data = json.loads(existing_data)  # Deserialize the JSON string to a dictionary
                existing_data.update(properties)
                self.redis.set(key, json.dumps(existing_data))  # Serialize back to JSON
    
            # Update properties in Aura DB
            with self.driver.session() as session:
                query = "SET " + ", ".join([f"w.{key} = ${key}" for key in properties.keys()])
                session.run(
                    f"""
                    MATCH (w:Word {{name: $word}})
                    {query}
                    """,
                    word=word, **properties
                )
            print(f"Properties for word '{word}' updated successfully!")
    
        if relationship and related_word:
            # Ensure the related word exists
            if not self.validate_existence(related_word):
                print(f"Related word '{related_word}' does not exist. Relationship creation aborted.")
                return
    
            # Update relationships in Aura DB
            with self.driver.session() as session:
                # Check if the relationship already exists
                existing_relationship = session.run(
                    """
                    MATCH (w1:Word {name: $word})-[r]->(w2:Word {name: $related_word})
                    RETURN type(r) AS relationship
                    """,
                    word=word, related_word=related_word
                ).single()
    
                if existing_relationship:
                    print(f"Overwriting existing relationship '{existing_relationship['relationship']}' with '{relationship}'.")
                    session.run(
                        """
                        MATCH (w1:Word {name: $word})-[r]->(w2:Word {name: $related_word})
                        DELETE r
                        """,
                        word=word, related_word=related_word
                    )
    
                # Create the new relationship
                session.run(
                    """
                    MATCH (w1:Word {name: $word}), (w2:Word {name: $related_word})
                    MERGE (w1)-[:`""" + relationship + """`]->(w2)
                    """,
                    word=word, related_word=related_word
                )
    
            print(f"Relationship '{relationship}' created/updated between '{word}' and '{related_word}'.")


    def delete_node(self, word):
        """Delete a word node from both Redis and Aura DB if it exists."""
        if not self.validate_existence(word):
            print(f"Word '{word}' does not exist. Deletion aborted.")
            return

        confirmation = input(f"Are you sure you want to delete the word '{word}'? Type the word name to confirm: ").strip()
        if confirmation != word:
            print("Deletion aborted. Confirmation failed.")
            return

        # Remove from Redis
        self.redis.delete(word)

        # Remove from Aura DB
        with self.driver.session() as session:
            session.run(
                """
                MATCH (w:Word {name: $word})
                DETACH DELETE w
                """,
                word=word
            )
        print(f"Word '{word}' deleted successfully!")

    def delete_all_key_from_redis(self, pattern='*'):
        """Delete all keys in Redis matching the given pattern with a colorful progress bar."""
        keys = self.get_all_keys(pattern)
        
        if not keys:
            print("No keys found in Redis to delete.")
            return

        print("Deleting keys from Redis...")
        for _ in tqdm(keys, desc="Deleting", unit="key", ncols=80, colour='red'):
            self.redis.delete(_)

        print(f"{Fore.GREEN}Deleted {len(keys)} keys from Redis.{Style.RESET_ALL}")
    
    def query_word_with_relationships(self, word):
        """Query a word node and its relationships from Redis and Aura DB, with optimization."""
        # Try to retrieve data from Redis
        data = self.redis.get(word)
        word_data = None  # Initialize word data variable
        if data:
            word_data = json.loads(data)  # Deserialize the JSON data
            print(f"Data for '{word}' found in Redis:")
            print("Properties:", word_data)
        else:
            print(f"Data for '{word}' not found in Redis. Checking Aura DB...")
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (w:Word {name: $word})
                    RETURN w
                    """,
                    word=word
                ).single()
    
                if result:
                    word_data = dict(result["w"])
                    print("Properties:", word_data)
                    self.redis.set(f"lexicon:{word}", json.dumps(word_data))  # Cache data in Redis
                else:
                    print(f"Word '{word}' does not exist in Aura DB.")
                    create_prompt = input(f"Word '{word}' does not exist. Do you want to create it? (yes/no): ").strip().lower()
                    if create_prompt == 'yes':
                        self.manager.create_word(word)
                    return None  # Exit if word does not exist
    
        # Fetch relationships from Aura DB
        relationships = []
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (w:Word {name: $word})-[r]->(related:Word)
                RETURN type(r) AS relationship, related
                """,
                word=word
            )
            relationships = [
                {"relationship": record["relationship"], "related_word": dict(record["related"])}
                for record in result
            ]
    
        if relationships:
            print("Relationships:")
            for rel in relationships:
                print(f"  - Relationship: {rel['relationship']}")
                print(f"    Related Word Properties: {rel['related_word']}")
        else:
            print("No relationships found for this word.")
    
        return {
            "word_properties": word_data,
            "relationships": relationships
        }


    def import_from_csv(self, file_path):
        """Import data from CSV into Redis and Aura DB."""
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                word = row['word']
                pos = row['POS']
                sentiment = row['sentiment']
                sentiment_score = float(row['sentiment_score']) if row['sentiment_score'] else None
                meaning = row['meaning']

                self.create_word_node(word, pos, sentiment, sentiment_score, meaning)

    def get_all_keys(self, pattern="*"):
        return self.redis.keys(pattern)
        
    def count_total_words_in_redis(self):
        """Count the total number of words stored in Redis."""
        total = 0

        # Adjust prefix to match your key storage standard, such as "lexicon:*"
        for key in self.get_all_keys("lexicon:*"):
            total += 1

        return total
                
class PromptWindow:
    def __init__(self, manager):
        """Initialize the prompt window with a Neo4jRedisLexiconManager instance."""
        self.manager = manager

    def show_menu(self):
        while True:
            print("\n--- Lexicon Manager Menu ---")
            print("1. Create a new word node")
            print("2. Create nodes with relationship")
            print("3. Query a word node")
            print("4. Update a word node")
            print("5. Delete a word node")
            print("6. Exit")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.create_word()
            elif choice == "2":
                self.create_nodes_with_relationship()
            elif choice == "3":
                self.query_word()
            elif choice == "4":
                self.update_word()
            elif choice == "5":
                self.delete_word()
            elif choice == "6":
                print("Exiting the prompt. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

    def create_word(self):
        word = input("Enter the word: ").strip()
        pos = input("Enter part of speech (POS): ").strip()
        sentiment = input("Enter sentiment (positive/negative/neutral): ").strip()
        sentiment_score = input("Enter sentiment score (0.0 to 1.0): ").strip()
        meaning = input("Enter the meaning: ").strip()

        try:
            sentiment_score = float(sentiment_score) if sentiment_score else None
        except ValueError:
            sentiment_score = None

        self.manager.create_word_node(word, pos, sentiment, sentiment_score, meaning)
        print(f"Word '{word}' created successfully!")

    def create_nodes_with_relationship(self):
        """User interface to create two nodes and a relationship between them."""
        word1 = input("Enter the first word: ").strip()
        word1_pos = input("Enter part of speech (POS) for the first word: ").strip()
        word1_sentiment = input("Enter sentiment (positive/negative/neutral) for the first word: ").strip()
        word1_meaning = input("Enter the meaning for the first word: ").strip()

        word2 = input("Enter the second word: ").strip()
        word2_pos = input("Enter part of speech (POS) for the second word: ").strip()
        word2_sentiment = input("Enter sentiment (positive/negative/neutral) for the second word: ").strip()
        word2_meaning = input("Enter the meaning for the second word: ").strip()

        allowed_relationships = ["SYNONYM_OF", "ANTONYM_OF", "HYPERNYM_OF", "HYPONYM_OF", "MERONYM_OF", "HOLONYM_OF"]
        while True:
            relationship = input(f"Enter the relationship between the words ({', '.join(allowed_relationships)}): ").strip().upper()
            if relationship in allowed_relationships:
                break
            print(f"Invalid relationship type: '{relationship}'. Allowed types are: {', '.join(allowed_relationships)}.")

        word1_properties = {
            "POS": word1_pos,
            "sentiment": word1_sentiment,
            "meaning": word1_meaning
        }

        word2_properties = {
            "POS": word2_pos,
            "sentiment": word2_sentiment,
            "meaning": word2_meaning
        }

        self.manager.create_nodes_with_relationship(
            word1,
            word1_properties,
            word2,
            word2_properties,
            relationship
        )
        
    def query_word(self):
        """Query a word node by taking user input and returning its properties and relationships."""
        word = input("Enter the word to query: ").strip()  
        result = self.manager.query_word_with_relationships(word)  # Call the function to fetch word data and relationships

    def update_word(self):
        word = input("Enter the word to update: ").strip()
        print("Enter new properties (leave blank to skip):")
        pos = input("New part of speech (POS): ").strip()
        sentiment = input("New sentiment (positive/negative/neutral): ").strip()
        sentiment_score = input("New sentiment score (0.0 to 1.0): ").strip()
        meaning = input("New meaning: ").strip()
    
        properties = {}
        if pos:
            properties["POS"] = pos
        if sentiment:
            properties["sentiment"] = sentiment
        if sentiment_score:
            try:
                properties["sentiment_score"] = float(sentiment_score)
            except ValueError:
                print("Invalid sentiment score. Skipping.")
        if meaning:
            properties["meaning"] = meaning
    
        if properties:
            self.manager.update_node_or_relationship(word, properties=properties)
    
        update_relationship = input("Do you want to update/create a relationship for this word? (yes/no): ").strip().lower()
        if update_relationship == "yes":
            related_word = input("Enter the related word: ").strip()
            allowed_relationships = ["SYNONYM_OF", "ANTONYM_OF", "HYPERNYM_OF", "HYPONYM_OF", "MERONYM_OF", "HOLONYM_OF"]
            while True:
                relationship = input(f"Enter the relationship ({', '.join(allowed_relationships)}): ").strip().upper()
                if relationship in allowed_relationships:
                    break
                print(f"Invalid relationship type. Allowed types are: {', '.join(allowed_relationships)}.")
    
            self.manager.update_node_or_relationship(word, relationship=relationship, related_word=related_word)

    def delete_word(self):
        word = input("Enter the word to delete: ").strip()
        self.manager.delete_node(word)

    def import_csv(self):
        file_path = input("Enter the path to the CSV file: ").strip()
        try:
            self.manager.import_from_csv(file_path)
            print("Data imported successfully from CSV.")
        except Exception as e:
            print(f"Failed to import data: {e}")

    def sync_db_to_redis(self):
        self.manager.sync_aura_to_redis()
        print("Data synced from Aura DB to Redis.")

    def count_total_words_in_redis(self):
        print(f"Total count of keys in Redis: {self.manager.count_total_words_in_redis()}")
