import logging
import sys
import os
from word2vec import Word2Vec, Sent2Vec, LineSentence
import io
import nltk
from nltk.tokenize import sent_tokenize
from nltk.stem import *
from collections import defaultdict
import math
import pdb
stemmer = SnowballStemmer("english", ignore_stopwords=False)

class SentencesRetriever():
	
	def __init__(self, article_filename):
		self.sentence_list = []
		self.lower2origin = {}
		with io.open(article_filename, 'r', encoding='utf8') as f:
			for line in f:
				line = line.strip()
				tmp_list = sent_tokenize(line)
				for sentence in tmp_list:
					self.lower2origin[sentence.lower()] = sentence
					self.sentence_list.append(sentence.lower())
				#self.sentence_list += tmp_list

	'''
		Retrieve the sentences using tf-idf

		@input: string of the input question and a constant K
		@output: return top K likely results
	'''
	def retrieve_sentences(self, question, K=10):
		tmp_list = [question] + self.sentence_list
		sentences = {}
		sentence2id = {}
		id2sentence = {}
		idx = 0
		for line in tmp_list:
			line = line.strip()

			sentence2id[idx] = line
			id2sentence[line] = idx
			

			terms = line.split(' ')
			stems = [stemmer.stem(term) for term in terms]
			bow = defaultdict(int)
			for stem in stems:
				bow[stem] += 1
			sentences[idx] = bow 
			idx += 1
		questionBOW = sentences[0]
		qlen = 0.0
		for stem in questionBOW:
			qlen += questionBOW[stem]

		del sentences[0]
		sentencesBOW = sentences

		N = len(sentencesBOW)
		df = {}
		for stem in questionBOW:
			cnt = 0.0
			for key in sentencesBOW:
				bow = sentencesBOW[key]
				if stem in bow:
					cnt += 1.0
			df[stem] = cnt

		sentences_score = {}
		for key in sentencesBOW:
			bow = sentences[key]
			score = 0.0
			for stem in questionBOW:
				if stem in bow:
					tf = bow[stem]
					stem_df = df[stem]
					score += tf*max(math.log((N-stem_df+0.5)/(stem_df+0.5)), 0)
			# lenth = 0
			# for stem in bow:
			# 	lenth += bow[stem]
			# score = score/lenth
			sentences_score[self.lower2origin[sentence2id[key]]] = score
		sentences_score_list = [(sentences_score[k], k) for k in sentences_score]
		sentences_score_list = sorted(sentences_score_list)
		sentences_score_list = sentences_score_list[::-1]
		K = min(K, len(sentences_score_list))
		return [tup[1] for tup in sentences_score_list[0:K]]

	'''
		Sort the list of sentences by cosine similarity

		@input: file name of the word2vec model & list the candidate sentences & question
		@output: re-ranked candidates
	'''
	def sort_vectorized_sentences(self, word2vec_model, sentences, question):
		sent_file = "my_sent.txt"
		with io.open(sent_file, 'w', encoding='utf8') as f:
			f.write(question+u"\n")
			for sentence in sentences:
				f.write(sentence+u"\n")
		model = Sent2Vec(LineSentence(sent_file), model_file=word2vec_model)
		sim = []
		for i in range(1, len(sentences)+1):
			cos = model.similarity(0, i)
			sim.append((cos, sentences[i-1]))
		sim = sorted(sim)
		sim = sim[::-1]
		os.remove(sent_file)
		return [tup[1] for tup in sim]


if __name__ == '__main__':
	filename = sys.argv[1] #any wiki articles (raw text)
	word2vec_model = sys.argv[2] #words.txt.model
	# rtv = SentencesRetriever(filename)
	# sentences = rtv.retrieve_sentences("how far is delta leonis away from earth?")
	# print sentences 
	# print rtv.sort_vectorized_sentences(word2vec_model, sentences, "how far is delta leonis away from earth?")