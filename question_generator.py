import os
from nltk.parse import stanford
from nltk.tag import StanfordPOSTagger
from nltk import word_tokenize
import graphviz

os.environ['STANFORD_PARSER'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/jars/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/stanford-parser-full-2018-02-27/stanford-parser-3.9.1-models.jar'


parser = stanford.StanfordDependencyParser()

# dep_list = list(result.triples())
# print()
# print()
# for thisTuple in dep_list:
#     if thisTuple[1] not in ('dep', 'appos'):
#         print(thisTuple)
#
#
# # GUI
# for line in sentences:
#     for sentence in line:
#         print(sentence)

from collections import defaultdict
from stanfordcorenlp import StanfordCoreNLP
import json
from nltk.tree import *

class StanfordNLP:
    def __init__(self, host='http://localhost', port=9000):
        self.nlp = StanfordCoreNLP(host, port=port,
                                   timeout=30000)  # , quiet=False, logging_level=logging.DEBUG)
        self.props = {
            'annotators': 'tokenize,ssplit,pos,lemma,ner,parse,depparse,dcoref,relation',
            'pipelineLanguage': 'en',
            'outputFormat': 'json'
        }

    def word_tokenize(self, sentence):
        return self.nlp.word_tokenize(sentence)

    def pos(self, sentence):
        return self.nlp.pos_tag(sentence)

    def ner(self, sentence):
        return self.nlp.ner(sentence)

    def parse(self, sentence):
        return Tree.fromstring(self.nlp.parse(sentence))

    def dependency_parse(self, sentence):
        return self.nlp.dependency_parse(sentence)

    def annotate(self, sentence):
        return json.loads(self.nlp.annotate(sentence, properties=self.props))

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


def getNodes(parent):
    for node in parent:
        if type(node) is Tree:
            if node.label() == 'ROOT':
                print("======== Sentence =========")
                print("Sentence:", " ".join(node.leaves()))
            else:
                print("Label:", node.label())
                print("Leaves:", node.leaves())

            getNodes(node)
        else:
            print("Word:", node)

if __name__ == '__main__':
    sNLP = StanfordNLP()
    text = 'Jefferson (1743–1826), who is the third U.S. President, is an amazing guy.'
    # text = 'Jefferson studied many subjects, like the artist Da Vinci, in his childhood.'
    print("Annotate:", sNLP.annotate(text))
    print("POS:", sNLP.pos(text))
    print("Tokens:", sNLP.word_tokenize(text))
    print("NER:", sNLP.ner(text))
    t = sNLP.parse(text)
    print("Parse:", t)
    print("Dep Parse:", sNLP.dependency_parse(text))

    sentences = parser.raw_parse(text)
    getNodes(t)
    # for line in list(t.subtrees()):
    #     # for sentence in line:
    #     #     print(sentence.label(0)==',')
    #     print(line.treepositions())
    # for line in sentences:
    #     for this in line:
    #         print(this)
    result = sentences.__next__()
    print(result.to_dot())
    print(list(result.triples()))