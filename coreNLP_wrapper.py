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

os.environ['CLASSPATH'] = '/home/syntaxsentinels/dry_run/121005/stanford-corenlp-full-2018-02-27'
os.environ['STANFORD_PARSER'] = '/home/syntaxsentinels/dry_run/121005/stanford-parser-full-2015-12-09/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = '/home/syntaxsentinels/dry_run/121005/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'

'''
os.environ['CLASSPATH'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27'
os.environ['STANFORD_PARSER'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'
'''
'''
os.environ['CLASSPATH'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/jars'
os.environ['STANFORD_MODELS'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/models'
'''

class StanfordNLP:
    def __init__(self, host='http://nlp02.lti.cs.cmu.edu', port=9000):
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
        self.url = "http://nlp02.lti.cs.cmu.edu:9000"

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

    #def dependency_parse(self, sentence):
    #    return self.nlp.dependency_parse(sentence)

    def dependency_parse(self, sentence):
        return self.nlp_depParser.raw_parse(sentence)

    def parser_sents(self, passage):
        return self.nlp_parser.raw_parse_sents(passage, )

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



  
