# Data-Engineering-Assignment
Build a Malay Lexicon.

# ---------------------------------  Hduser ---------------------------------------

	(HDFS) start-dfs.sh
	(YARN) start-yarn.sh
	(HBASE) start-hbase.sh
	(THRIFT service) hbase thrift start -p 9090 &
	(ZOOKEEPER) zookeeper-service-start.sh $KAFKA_HOME/config/zookeeper.properties &
	(KAFKA Service) kafka-service-start.sh $KAFKA_HOME/config/server.properties &

To check: ~$ jps

# ---------------------------------- Student ---------------------------------------
(Environment) 

nano ~/.profile

# (insert these all inside the profile)

>>>>>>>>

	export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
	export HADOOP_HOME=/home/hduser/hadoop3
	export PATH=$PATH:$HADOOP_HOME/bin
	export PATH=$PATH:$HADOOP_HOME/sbin
	export HADOOP_STREAMING=$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar

	export SPARK_HOME=/home/hduser/spark
	export PATH=$PATH:$SPARK_HOME/bin

	export KAFKA_HOME=/home/hduser/kafka
	export PATH=$PATH:$KAFKA_HOME/bin

	export HBASE_HOME=/home/hduser/hbase                    
	export PATH=$HBASE_HOME/bin:$PATH

				                              <<<<<<<<<<<<<<
# (after that activates the env)
source 	~/.profile

# (Install Redis)
1. sudo apt update
2. sudo apt install redis-server

# (Configure Redis)
3. sudo nano /etc/redis/redis.conf

4. change to >> supervised systemd

5. sudo systemcl restart redis-server

# (then activate the virtual env, for example:) 
source de-ass/ass-venv/bin/activate  

# ---------------------------- Under Virtual Environment -------------------------------
(Install required packages or libraries)

pip install pyspark pyvis py2neo networkx scikit-learn numpy transformers tqdm colorama redis happybase pymongo neo4j kafka-python-ng 

--------------------------------------------------------------------------------------

# ------------------------------------Deactivate the virtual Env --------------------------------------
1. (ass-venv) student ~$ deactivate
2. exit
3. hduser ~$ kafka-server-stop.sh (Wait for about 30 seconds before performing the next step.)
4. hduser ~$ zookeeper-server-stop.sh (Wait for about 30 seconds before performing the next step.)
5. hduser ~$ kill -9 5055 ('5055' is code of your thrift services)
6. hduser ~$ stop-hbase.sh
7. hduser ~$ stop-yarn.sh
8. hduser ~$ stop-dfs.sh
9. exit
------------------------------------------------------------------------------------------------------


#                                            ~~~~~~~~~~~~~~~~~~ Wish this docs can save your time ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

