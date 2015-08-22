from pyspark.sql import SQLContext, Row
from pyspark.mllib.regression import LabeledPoint
from pyspark.mllib.linalg import Vectors
from pyspark.mllib.linalg import SparseVector
from pyspark.mllib.classification import LogisticRegressionWithLBFGS
from BeautifulSoup import BeautifulSoup
from nltk.corpus import stopwords
from pyspark.ml.feature import Word2Vec
from pyspark.streaming import StreamingContext
import nltk.data
import re


def paragraph_to_wordlist( raw_review):
    # Function to clean data
    #
    # removing html tags using BeautifulSoup api
    review_text = BeautifulSoup(raw_review).text
    #  
    # removing non-alpahbetical data
    review_text = re.sub("[^a-zA-Z]"," ", review_text)
    #
    # converting to consistant lowercase
    words = review_text.lower().split()
    return(words)

def paragraph_to_sentences(review,tokenizer):
    # Function to clean data, to create sentences from paragraphs of reviews.
    #
    # Use NLTK tokenizer to form sentences from the paragraph reviews
    raw_sentences = tokenizer.tokenize(review.strip())
    #
    # Loop over each sentence in the paragraph
    sentences = []
    for raw_sentence in raw_sentences:
        # Skipping empty sentances
        if len(raw_sentence) > 0:
            # clean sentences using paragraph_to_wordlist 
            sentences.append(paragraph_to_wordlist(raw_sentence))
    return sentences

#instantiating tokenizer for splitting sentences
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

#getting the set of stopwords
stops = set(stopwords.words("english")) 

#instantiating the list for sentences
new_sentence = []

#Training the Word2Vec model
#Fetching the unlabelled data from S3.
u_lines = sc.textFile("s3://spark-project-data/unlabeledTrainData.tsv")
#removing the header
u_rows = u_lines.zipWithIndex().filter(lambda (row,index): index > 0).keys()
#getting values of each column(spliting by tab)
u_parts = u_rows.map(lambda l: l.split("\t"))
#Creating a RDD of Rows contining list of lines of each review and collecting it as a list
u_review = u_parts.map(lambda p: paragraph_to_sentences(p[1],tokenizer)).collect()
#Joining the list together to form a single list
for review in u_review:
    new_sentence += review

#Creating a RDD of sentences from the list
u_sentance = sc.parallelize(new_sentence)
#Creaing a RDDD of rows
u_sentenceDF = u_sentance.map(lambda s: Row(sentence=s))
#Converting it to a dataframe
sentenceDF = sqlContext.createDataFrame(u_sentenceDF,["sentence"])
#instantiating the word2Vec Model
word2vec = Word2Vec()
#Training the model for vectorsize 300
wvModel = Word2Vec(vectorSize=300,minCount=40 ,seed=42, inputCol="sentence", outputCol="features").fit(sentenceDF)

#Training the Classification algorithm
#Fetching the data from S3
lines = sc.textFile("s3://spark-project-data/labeledTrainData.tsv")
#Removing the header
rows = lines.zipWithIndex().filter(lambda (row,index): index > 0).keys()
#Getting the columns
parts = rows.map(lambda l: l.split("\t"))
#creating RDD of reviews
review = parts.map(lambda p: Row(id=p[0], label=float(p[1]), 
	sentence=paragraph_to_wordlist(p[2])))

#creating the dataframe
reviewDF = sqlContext.createDataFrame(review)
#transforming the words to vectors using the trained model
transformDF = wvModel.transform(reviewDF)
#segregating the labels and features
selectData = transformDF.select("label","features","id")
#Creating RDD of LabeledPoints
lpSelectData = selectData.map(lambda x : (x.id, LabeledPoint(x.label,x.features)))
#Spliting the data for training and test
(trainingData, testData) = lpSelectData.randomSplit([0.9, 0.1])
# training the Logistic regression with LBFGS model
lrm = LogisticRegressionWithLBFGS.train(trainingData.map(lambda x: x[1]), iterations=10)
#fetching the labels and predictions for test data
labelsAndPreds = testData.map(lambda p: (p[0],p[1].label, lrm.predict(p[1].features)))
#calculating the accuracy and printing it.
accuracy = labelsAndPreds.filter(lambda (i, v, p): v == p).count() / float(testData.count())
print("Accuracy = " + str(accuracy))

text = sc.textFile("s3://spark-sentimentanalysis/file.txt")
testreview = text.map(lambda t: Row(sentence = paragraph_to_wordlist(t)))
testreviewDF = sqlContext.createDataFrame(testreview)
testVect = wvModel.transform(testreviewDF).select("features")
sentiment = lrm.predict(testVect.first().features)
print 'sentiment' + str(sentiment)
sc.parallelize(str(sentiment)).saveAsTextFile("s3://spark-sentimentanalysis/result/")












