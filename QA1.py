import re
import os
import requests
from nltk.parse import stanford
from nltk.tokenize import word_tokenize
from collections import defaultdict
from stanfordcorenlp import StanfordCoreNLP
import json
from nltk.tree import *
from testscript import *
import string
import nltk
import sys
import copy

os.environ['CLASSPATH'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27'
os.environ['STANFORD_PARSER'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'
'''
os.environ['CLASSPATH'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/jars'
os.environ['STANFORD_MODELS'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/models'
'''
eps = 1e-10
class StanfordNLP:
    def __init__(self, host='http://localhost', port=9000):
        self.nlp = StanfordCoreNLP(host, port=port,
                                   timeout=30000)  # , quiet=False, logging_level=logging.DEBUG)

        # self.nlp = StanfordCoreNLP(r'/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27')
        self.nlp_depParser = stanford.StanfordDependencyParser()
        self.nlp_parser = stanford.StanfordParser()

        self.props = {
            'annotators': 'coref',
            'pipelineLanguage': 'en'  # ,
            # 'outputFormat': 'json'
        }
        self.url = "http://localhost:9000"

    def word_tokenize(self, sentence):
        return self.nlp.word_tokenize(sentence)

    def pos(self, sentence):
        return self.nlp.pos_tag(sentence)

    def ner(self, sentence):
        return self.nlp.ner(sentence)

    def coref(self, text):
        if sys.version_info.major >= 3:
            text = text.encode('utf-8')
        props = {'annotators': 'coref', 'pipelineLanguage': 'en'}
        r = requests.post(self.url, params={'properties': str(props)}, data=text,
                          headers={'Connection': 'close'})
        return r.text

    def parse(self, sentence):
        return ParentedTree.convert(Tree.fromstring(self.nlp.parse(sentence)))

    # def dependency_parse(self, sentence):
    #     return self.nlp.dependency_parse(sentence)
    def dependency_parse(self, sentence):
        return self.nlp_depParser.raw_parse(sentence)

    def parser_sents(self, passage):
        return self.nlp_parser.raw_parse_sents(passage,)

    @staticmethod
    def tokens_to_dict(_tokens):
        tokens = defaultdict(dict)
        for token in _tokens:
            tokens[int(token['index'])] = {
                'word': token['word'],
                'lemma': token['lemma'],
                'pos': token['pos'],
                'ner': token['ner']
            }
        return tokens


class QA():
    def __init__(self):
        self.sNLP = StanfordNLP()
        self.dropType = {}
        self.dropType['What'] = ['NP','asdf']
        self.auxWord = ['did','do','does']
        self.candidateAnswer = []
        self.candidateSentence = []

    def qstType(self, qst):
        return 'What'


    def dropFragment(self,myParent,qstType):
        
        flag = 0
        
        for node in myParent:
            node.pretty_print()

            if self.dropTime > self.dropTotal:
                return myParentmyParenta
            if node.label() in self.dropType[qstType]:
                #print('???')
                self.dropTime += 1
                if self.dropTime > self.dropTotal:
                    myParent.remove(node)
                    self.candidateAnswer.append(node.leaves())
                    self.findFlag  =1
                return myParent
                #if node.parent() is not None:  ### recursive to go in depth of the tree
            self.dropFragment(node,qstType)
            if node.label() == 'ROOT' and self.findFlag:
                self.candidateSentence.append(node.leaves())
     
        return myParent



    def answer(self, txt, qst):
        qstType = self.qstType(qst)

        #x = list(self.sNLP.pos(qst))
        #print(x)
        tokens = self.sNLP.word_tokenize(txt)

        self.candidateAnswer = []
        self.candidateSentence = []

        tree = self.sNLP.parser_sents([txt,])
        for i in tree:
            self.dropTotal = 0
            self.dropFlag = 1
            while self.dropFlag:
                self.findFlag = 0
                nowTree = copy.deepcopy(i)
                self.dropTime = 0
                nowTree = self.dropFragment(nowTree,qstType)
                if self.dropTime <= self.dropTotal:
                    self.dropFlag = 0
                self.dropTotal += 1 
                print(self.dropTime,self.dropTotal)
                print('--------------')
            
            #res = self.dropFragment(i,qstType)
        '''
        dep_parse_Tree = dep_parse_Tree.__next__()
        triples_list = list(dep_parse_Tree.triples())
        print(triples_list)
        for x in triples_list:
            print(x[2][0])
        '''

        tokens = self.sNLP.word_tokenize(qst)
        tokens.pop(0)
        tokens.pop(-1)
        if tokens[0] in self.auxWord:
            tokens.pop(0)
        for i in range(len(self.candidateSentence)):
            nowSentence = self.candidateSentence[i]
            nowSentence.pop(-1)
            if self.candidateSentence[i] == tokens:
                print("answer is:")
                print(' '.join(self.candidateAnswer[i]))



if __name__ == '__main__':
    QA = QA()

    txt = 'we give a book to Mary.'
    qst = 'Who give a book to Mary?'

    QA =  QA.answer(txt,qst)

  