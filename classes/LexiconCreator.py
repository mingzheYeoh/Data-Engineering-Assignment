import requests
import re

class lexiconRawDataCollector:
    def __init__(self):
        self.api_url = "https://ms.wikipedia.org/w/api.php"

    def getCategoryMembers(self, category, limit):
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Kategori:{category}",
            "cmlimit": limit,
            "format": "json"
        }
        response = requests.get(self.api_url, params=params)
        data = response.json()
        return [item["title"] for item in data.get("query", {}).get("categorymembers", [])]
    
    def fetchArticleText(self, title):
        params = {
            "action": "query",
            "prop": "extracts",
            "titles": title,
            "explaintext": True, 
            "format": "json"
        }
        response = requests.get(self.api_url, params=params)
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        
        for page_id, page_data in pages.items():
            if "extract" in page_data:
                return page_data["extract"]
        return ""

    def articlesRDDToDFTransformation(self, spark, articles):
        articleRDD = spark.sparkContext.parallelize(articles)
        cleanWordsRDD = articleRDD.flatMap(self.fetchAndCleanArticle)
        cleanWordsDF = spark.createDataFrame(cleanWordsRDD.map(lambda x: (x,)), ["word"])
        return cleanWordsDF
    
    def cleanText(self, text_content):
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text_content.lower())
        return words

    def fetchAndCleanArticle(self, title):
        text_content = self.fetchArticleText(title)
        cleaned_words = self.cleanText(text_content)
        return cleaned_words

    def exportToCSV(self, df, output_path):
        outDF = df.groupBy("word").count() ##individual part lwm
        outDF.coalesce(1).write.csv(output_path, header=True, mode="overwrite")
        print(f"Cleaned words with frequencies saved to {output_path}")
