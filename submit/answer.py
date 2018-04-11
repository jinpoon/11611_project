from sentence_retrieve import SentencesRetriever
import __future__
from QA import *
import sys
import io

if __name__ == '__main__':
	
	filename = sys.argv[1]
	questionfile = sys.argv[2]
	model_file = sys.argv[3]
	retriever = SentencesRetriever(filename)
	qa = QA()
	with io.open(questionfile, 'r', encoding='utf8') as f:
		for line in f:
			question = line.strip()
			sl = retriever.retrieve_sentences(question)
			#sl = retriever.sort_vectorized_sentences(model_file, sl, question)
			qa.answer(sl, question)