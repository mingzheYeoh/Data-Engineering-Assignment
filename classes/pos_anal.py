# Author: Wong Shu Han 
# Created: 11 December 2024

from neo4j import GraphDatabase
from collections import Counter

class POSAnalyzer:
    
    # Initialize the Neo4j driver with the given connection details.
    def __init__(self, uri, user, password):
       self.driver = GraphDatabase.driver(uri, auth=(user, password))

    # Close the Neo4j connection.
    def close(self):
        self.driver.close()
#--------------------------------------------------------------------------------------------------------------------------------------------------------
    # Fetch POS distribution from Neo4j, output = POS, count, percentage
    def fetch_pos_distribution(self):

        # Cypher query to fetch words and their POS
        query = """
        MATCH (w:Word)
        RETURN w.name AS word, w.POS AS pos
        """
        
        # Initialize POS counter
        pos_counter = Counter()

        # Execute the query within a session
        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                pos = record.get("pos", "UNKNOWN")  # Handle missing POS with 'UNKNOWN'
                pos_counter[pos] += 1
        
        # Calculate the total number of POS then calculate their percentage
        total_count = sum(pos_counter.values())
        pos_percentage = {pos: (count / total_count) * 100 for pos, count in pos_counter.items()}
        
        return pos_counter, pos_percentage
#--------------------------------------------------------------------------------------------------------------------------------------------------------
    # Fetch total number of words
    def fetch_total_word_count(self):
        # Cypher query to fetch the total number of words
        query = """
        MATCH (w:Word)
        RETURN count(w) AS total_words
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            total_words = result.single().get("total_words", 0)  # Default to 0 if no words are found
        
        return total_words
#--------------------------------------------------------------------------------------------------------------------------------------------------------
    # Fetch numbers of distinct POS 
    def fetch_distinct_pos_count(self):
        pos_distribution, _ = self.fetch_pos_distribution() # To unpack tuple, get pos_distribution (POS and counts) and ignore the percentage
        return len(pos_distribution)
#--------------------------------------------------------------------------------------------------------------------------------------------------------
    def display_general_counts(self):
        # Fetch total word and distinct pos count
        total_word_count = self.fetch_total_word_count()
        distinct_pos_count = self.fetch_distinct_pos_count()
        
        # Display total word count and distinct POS count
        print(f"Total number of words available in the database: {total_word_count}")
        print(f"Number of distinct POS: {distinct_pos_count}")
#--------------------------------------------------------------------------------------------------------------------------------------------------------
    # Get the distribution, sort by count, then print number of record determined by user in the order required by user (default descending)
    def display_sorted_pos(self, order="desc", limit=None):
        pos_distribution, pos_percentage = self.fetch_pos_distribution()

        # Sort the POS tags by count in the specified order and limit the number of output
        if order == "asc":
            reverse_order = False
        else:
            reverse_order = True
        sorted_pos_distribution = sorted(pos_distribution.items(), key=lambda x: x[1], reverse=reverse_order)

        if limit:
            sorted_pos_distribution = sorted_pos_distribution[:limit]
            
        # Display POS distribution with counts and percentages
        print("-" * 60)
        print(f"Part of Speech Distribution (Sorted by Count in {order.upper()} order):")
        for pos, count in sorted_pos_distribution:
            percentage = pos_percentage.get(pos, 0)  # Get the percentage for each POS
            print(f"{pos}: {count} ({percentage:.2f}%)")
#--------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # # Validation function to ask user enter 'asc' or 'desc', and number of output
    # def get_user_input_and_display(self):
    #     order = input("Enter sorting order (asc/desc): ").strip().lower()
    #     limit_input = input("Enter the number of POS to display (leave empty for all): ").strip()

    #     limit = None
    #     if limit_input:
    #         try:
    #             limit = int(limit_input)
    #             if limit <= 0:
    #                 print("Please enter a positive integer for the number of POS tags.")
    #                 return
    #         except ValueError:
    #             print("Invalid input. Please enter a valid number for the limit.")
    #             return
        
    #     if order in ["asc", "desc",""]:
    #         self.display_sorted_pos(order, limit)
    #     else:
    #         print("Invalid input. Please enter 'asc' for ascending or 'desc' for descending.")
    # Validation function to ask user to enter 'asc' or 'desc', and number of output
    def get_user_input_and_display(self):
        while True:
            # Ask for sorting order
            order = input("Enter sorting order (asc/desc, leave empty for descending): ").strip().lower()
            if order in ["asc", "desc", ""]:
                break  # Exit the loop if valid input
            else:
                print("Invalid input. Please enter 'asc' for ascending, 'desc' for descending, or leave empty for descending.")

        while True:
            # Ask for the number of POS tags to display
            limit_input = input("Enter the number of POS to display (leave empty for all): ").strip()
            if not limit_input:  # Empty input means show all
                limit = None
                break
            try:
                limit = int(limit_input)
                if limit > 0:
                    break  # Valid input, exit the loop
                else:
                    print("Please enter a positive integer for the number of POS tags.")
            except ValueError:
                print("Invalid input. Please enter a valid number for the limit.")

        # Call the function to display sorted POS tags
        self.display_sorted_pos(order, limit)






