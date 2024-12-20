#Author: Lai Yoke Yau

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, sum, explode, array_repeat
from neo4j import GraphDatabase

class WordLengthAnalyzer:
    def __init__(self, df: DataFrame = None, uri: str = None, username: str = None, password: str = None):
        """
        Initialize the WordLengthAnalyzer class.

        Args:
            df (DataFrame): Input Spark DataFrame containing 'wordLength' and 'count'.
            uri (str): Neo4j database URI.
            username (str): Neo4j username.
            password (str): Neo4j password.
        """
        self.df = df
        self.driver = None
        
        if uri and username and password:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            print("Connected to Neo4j successfully.")

    def close_connection(self):
        """Close the connection to Neo4j."""
        if self.driver:
            self.driver.close()
            print("Connection to Neo4j closed.")

    def wordLength_query(self):
        """
        Run a query on the Neo4j database to calculate word lengths and their counts.

        Returns:
            list[dict]: A list of dictionaries containing 'wordLength' and 'count'.
        """
        if not self.driver:
            raise ValueError("No Neo4j connection initialized.")
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (w:Word)
                WITH size(w.name) AS wordLength, count(*) AS count
                RETURN wordLength, count
                ORDER BY wordLength
            """)
            return [record.data() for record in result]

    def calculate_average_word_length(self) -> float:
        """
        Calculate the average word length using a weighted formula.

        Returns:
            float: The average word length.
        """
        total_weighted_length = self.df.select(
            sum(col("wordLength") * col("count")).alias("total_weighted_length")
        ).collect()[0][0]

        total_frequency = self.df.select(
            sum(col("count")).alias("total_frequency")
        ).collect()[0][0]

        if total_frequency == 0:  # Avoid division by zero
            return 0.0
        
        average_word_length = total_weighted_length / total_frequency
        return average_word_length

    def calculate_median_word_length(self) -> float:
        """
        Calculate the median word length by expanding the dataset based on counts.

        Returns:
            float: The median word length.
        """
        # Expand the dataset by frequency for the median calculation
        expanded_df = self.df.select(
            explode(array_repeat(col("wordLength"), col("count").cast("int"))).alias("expanded_wordLength")
        )

        # Calculate total count of rows
        total_count = expanded_df.count()

        # Sort the expanded dataset by word length
        sorted_df = expanded_df.orderBy("expanded_wordLength")

        # Calculate median
        if total_count % 2 == 1:  # Odd total count
            median_row = sorted_df.limit(total_count // 2 + 1).tail(1)[0]
            median_word_length = median_row["expanded_wordLength"]
        else:  # Even total count
            middle_two_rows = sorted_df.limit(total_count // 2 + 1).tail(2)
            median_word_length = (middle_two_rows[0]["expanded_wordLength"] + middle_two_rows[1]["expanded_wordLength"]) / 2

        return median_word_length

    def analyze(self) -> None:
        """
        Perform analysis to compute and display both average and median word lengths.
        """
        average = self.calculate_average_word_length()
        median = self.calculate_median_word_length()

        print(f"Average Word Length: {average}")
        print(f"Median Word Length: {median}")
