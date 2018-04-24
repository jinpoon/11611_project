from sentence_retrieve import SentencesRetriever
import __future__
from new_QG import *
import sys
import io
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
import string
from Corefer import preprocess_coref


if __name__ == '__main__':
	
	filename = sys.argv[1]
	# filename = "./data/set3/a6.txt"
	qsList = []
	n = int(sys.argv[2])
	# n = 30
	# with io.open(filename, 'r', encoding='utf8') as f:
	# 	sentenceList = []
	# 	for line in f:
	# 		sentences = sent_tokenize(line)
	# 		for sentence in sentences:
	# 			#print(sentence)
	# 			if (len(sentence.split(" ")) > 5 and
	# 				len(sentence.split(" ")) < 25 and
	# 				word_tokenize(sentence)[-1] in string.punctuation):
	# 				sentenceList.append(sentence)

	sentenceList = preprocess_coref(filename)
	qsList = askMe(sentenceList, n)
	minlen = min(len(qsList), n)
	qsList = qsList[:]
	for i in qsList:
		print(i[1])
		
