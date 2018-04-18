from sentence_retrieve import SentencesRetriever
import __future__
from QG11 import *
import sys
import io
import nltk
from nltk.tokenize import sent_tokenize

if __name__ == '__main__':
	
	filename = sys.argv[1]
	qsList = []
	n = int(sys.argv[2])
	with io.open(filename, 'r', encoding='utf8') as f:
		for line in f:
			sentences = sent_tokenize(line)
			for sentence in sentences:
				#print(sentence)
				qg = QG(sentence)
				tmp_list = qg.run(n)
				#print (tmp_list)
				qsList += tmp_list
		qsList = sorted(qsList)
		qsList = qsList[::-1]
		minlen = min(len(qsList), n)
		for i in qsList[0:minlen]:
			print(i[1])
		
