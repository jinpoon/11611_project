import nltk
from nltk import Tree, parse
from nltk import PCFG
from nltk.corpus import treebank
from nltk import treetransforms
from nltk import induce_pcfg
#from stat_parser import Parser
from nltk.parse import stanford
from nltk.grammar import Nonterminal, nonterminals, Production, ProbabilisticProduction
import os, io
import sys
import re
import six
import pdb
import math

os.environ['CLASSPATH'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27'
os.environ['STANFORD_PARSER'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'
eps = 1e-10

class QuestionEvaluator(object):
	"""docstring for QuestionEvaluator"""
	def __init__(self, productions_filename=None):
		super(QuestionEvaluator, self).__init__()
		self.parser = stanford.StanfordParser(encoding='utf8')
		if (productions_filename != None):
			self.read_productions(productions_filename)
		else:
			self.grammar = None

	def write_productions_to_file(self, productions_filename):
		assert (self.grammar != None)
		productions = self.grammar.productions()
		with io.open(productions_filename, 'w', encoding='utf8') as f:
			for p in productions:
				lhs = "%s" % p.lhs()
				rhs = " ".join(["%s"%s for s in p.rhs()])
				prob = "%f" % p.prob()
				f.write(lhs+u"+"+rhs+u"+"+prob+u"\n")

	def read_productions(self, productions_filename):
		productions = []
		with io.open(productions_filename, 'r', encoding='utf8') as f:
			for line in f:
				line = line.strip()
				components = line.split(u'+')
				lhs = Nonterminal(components[0])
				rhs = tuple([Nonterminal(nt.strip()) for nt in components[1].split(u' ')])
				prob = float(components[2])
				pp = ProbabilisticProduction(lhs, rhs, prob=prob)
				productions.append(pp)
		self.grammar = PCFG(Nonterminal('S'), productions)
		
	def generate_pcfg_productions(self, questionbank):
		productions = []

		with io.open(questionbank, 'r', encoding='utf8') as f:
			for line in f:
				line = line.strip()
				sent_text = nltk.sent_tokenize(line)

				for sentence in sent_text:
					#print sentence
					ss = self.parser.raw_parse_sents((sentence,))
					for k in ss:
						for s in k:
							buf = "%s" % s
							buf = six.text_type(buf)
							s1 = Tree.fromstring(buf)

							#get rid of the ROOT
							for node in s1:
								if node.label() == 'ROOT':
									continue
								else:
									s1 = node
									break
							s1.chomsky_normal_form(horzMarkov = 2)
							pdc = []
							for p in s1.productions():
								#remove the lexical production
								if not p.is_lexical():
									pdc.append(p)

							productions += pdc

		S = Nonterminal('S')
		self.grammar = induce_pcfg(S, productions)


	def traverse(self, node):
		assert (self.grammar != None)
		prob = 0.0
		length = 0
		if node.height() == 2:
			return (prob, length)
		lhs = Nonterminal(node.label())
		productions = self.grammar.productions(lhs)

		#find the productions from 
		flag = False
		rhs_list = []
		for c in node:
			rhs_list.append(Nonterminal(c.label()))
		tuple_rhs = tuple(rhs_list)
		for p in productions:
			if p.lhs() == lhs and p.rhs() == tuple_rhs:
				flag = True
				prob += math.log(p.prob())
				break
		if not flag:
			prob += math.log(eps)
		length += 1
		for c in node:
			ret = self.traverse(c)
			prob += ret[0]
			length += ret[1]
		return (prob, length)

	'''
	@param: sentence that needs to be evaluate
	@output: a grammartical probability
	'''
	def evaluate(self, sentence):
		ss = self.parser.raw_parse_sents((sentence, ))
		tree = None
		for k in ss:
			for s in k:
				buf = "%s" % s
				buf = six.text_type(buf)
				tree = Tree.fromstring(buf)
				for node in tree:
					if node.label() == 'ROOT':
						continue
					else:
						tree = node
						break
				tree.chomsky_normal_form(horzMarkov = 2)

		#print tree
		(prob, length) = self.traverse(tree)
		return prob/length

if __name__ == '__main__':
	questions = sys.argv[1]
	evaluator = QuestionEvaluator(productions_filename = "questionbank_pcfg.txt")

	# tups = []
	# with io.open(questions, 'r', encoding='utf8') as f:
		
	# 	for line in f:
	# 		line = line.strip()
	# 		if(line[0:2] == '--'):
	# 			symbol = '-'
	# 			line = line[2:]
	# 		else:
	# 			symbol = '+'
	# 		prob = evaluator.evaluate(line)
	# 		tups.append((prob, line, symbol))
	# tups = sorted(tups)
	# print tups


	#evaluator.generate_pcfg_productions(questionbank)
	#print evaluator.evaluate("Is Volta buried in the city of Pittsburgh?")
	#evaluator.write_productions_to_file('other_questionbank_pcfg.txt')
	#print evaluator.evaluate("When is the battery made?")
