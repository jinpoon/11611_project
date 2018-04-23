import os
import nltk
import sys
import io
from neuralcoref import Coref


def preprocess_coref(filename):
	textList = []
	with io.open(filename, 'r', encoding='utf-8') as f:
		coref = Coref()
		for line in f:
			line = line.strip()
			orginal_sentence_list = nltk.sent_tokenize(line)
			if(len(orginal_sentence_list) == 0):
				continue
			if len(orginal_sentence_list) == 1 and len(nltk.word_tokenize(orginal_sentence_list[0])) <= 4:
				continue
			paraL = []
			paraL.append(orginal_sentence_list[0])
			textList.append(orginal_sentence_list[0])
			for i in range(0, len(orginal_sentence_list) - 1):
				clusters = coref.one_shot_coref(utterances=orginal_sentence_list[i+1], context=orginal_sentence_list[i])
				resolved_utterance_text = (coref.get_resolved_utterances())[0]
				orginal_sentence_list[i+1] = resolved_utterance_text
				textList.append(resolved_utterance_text)
				paraL.append(resolved_utterance_text)
			# for s in paraL:
			# 	print s,
			# print "\n"
	return textList

if __name__ == '__main__':
	filename = sys.argv[1]
	print (preprocess_coref(filename))







