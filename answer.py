from sentence_retrieve import SentencesRetriever
import __future__
from QA import *
import sys
import io
import os
from Corefer import preprocess_coref

if __name__ == '__main__':
	
	filename = sys.argv[1]
	coref_segm_filename = filename+".corf"
	textlist = preprocess_coref(filename)
	with io.open(coref_segm_filename, 'w', encoding='utf8') as f:
		for s in textlist:
			f.write(s+u"\n")
	questionfile = sys.argv[2]
	model_file = 'words.txt.model'
	retriever = SentencesRetriever(coref_segm_filename)
	qa = QA()
	with io.open(questionfile, 'r', encoding='utf8') as f:
		for line in f:
			question = line.strip()
			sl = retriever.retrieve_sentences(question)
			#sl = retriever.sort_vectorized_sentences(model_file, sl, question)
			qa.answer(sl, question)
	os.remove(coref_segm_filename)