# Author: Lim Wai Ming

from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json
from datetime import datetime

class kafkaUtility:
    
    def inititateDataCollectionKafkaProducer(self, kafkaBroker, topic, values):
        try:
            producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'], 
                value_serializer=lambda v: json.dumps(v).encode('utf-8') 
            )
            print("Kafka producer initialized successfully.")
        
            topic = 'rawdata'
            producer.send(topic, value=values)
            producer.flush() 
            print(f"Data sent to Kafka topic '{topic}' successfully.")
        
        except KafkaError as e:
            print(f"Error occurred while sending to Kafka: {e}")
                
    
    def initiateDataCleaningConsumer(self, kafkaBroker, topic, refresherName, lexicon, spark):
        try:
            consumer = KafkaConsumer(
                topic,  
                bootstrap_servers=[kafkaBroker],  
                auto_offset_reset='earliest',  
                enable_auto_commit=True,  
                group_id='rawdata-consumer-group', 
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            print("Kafka consumer initialized successfully.")

            print(f"Listening to Kafka topic 'rawdata'...")
            for articles in consumer:
                print(f"Received message: {articles.value}")
                #Filter and clean data
                cleanWordsDF = lexicon.articlesRDDToDFTransformation(spark, articles)
                #CSVVVVVVVVVV
                currentDateTime = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
                refresherName = "LWM"
                output_path = f"storageCleanedCSV/cleaned_words_{currentDateTime}_{refresherName}.csv"
                lexicon.exportToCSV(cleanWordsDF, output_path)

        except Exception as e:
            print(f"Error occurred while consuming from Kafka: {e}")

