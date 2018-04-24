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
from coreNLP_wrapper import StanfordNLP
from QA_utils import *
import pdb
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# os.environ['CLASSPATH'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27'
# os.environ['STANFORD_PARSER'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser.jar'
# os.environ['STANFORD_MODELS'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'
'''
os.environ['CLASSPATH'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/jars'
os.environ['STANFORD_MODELS'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/models'
'''
eps = 1e-10


class QA():
    def __init__(self):
        self.sNLP = StanfordNLP()
        self.dropType = {}
        self.typeNer = {}
        self.typePro = {}
        self.initQstType()
        self.candidateAnswer = []
        self.candidateSentence = []
        self.qgPipeline = QGPipeline()
        self.threshold = 90

    def initQstType(self):
        self.typeSet = ['WHADJP', 'WHADVP', 'WHPP', 'WHAVP', 'WHNP']
        self.dropType['WHADJP'] = ['NP', 'CD']
        self.dropType['WHAVP'] = ['PP', 'SBAR']
        self.dropType['WHADVP'] = ['PP', 'SBAR']
        self.dropType['WHPP'] = ['PP']
        self.dropType['WHNP'] = ['NP']
        self.dropType['UK'] = ['NP', 'NN']
        self.auxWord = ['did', 'do', 'does', 'is', 'are', 'were', 'was']
        self.typePro['where'] = ['in', 'at', 'on', 'behind', 'next']
        self.typeNer['when'] = ['DATE']
        self.typeNer['where'] = ['CITY', 'STATE_OR_PROVINCE', 'ORGANIZATION', 'LOCATION', 'COUNTRY']

    def decideType(self, myParent):
        if self.qstFlag:
            return
        for node in myParent:
            # node.pretty_print()
            if self.qstFlag:
                return

            if isinstance(node, str): continue

            if node.label() in self.typeSet:
                self.thisType = node.label()
                myParent.remove(node)
                self.qstFlag = True
            self.decideType(node)
            if node.label() == 'ROOT':
                self.qstSim = node.leaves()
                self.qstSim = ' '.join(self.qstSim[:-1])

    def bin_answer(self, question, sent):
        bin_tags = set(["did", 'do', 'does', 'are', 'is', 'have', 'was','were', 'has'])
        question = question.lower()
        sent = sent.lower()
        q_tokens = word_tokenize(question)
        s_tokens = word_tokenize(sent)
        negations = set(['not', 'never', "aren't"])
        ans = ''
        # case 1: negations
        for neg in negations:
            if (neg in q_tokens) and (neg not in s_tokens):
                if ans == "No":
                    ans = "Yes"
                else:
                    ans = "No"
            if (neg in q_tokens) and (neg in s_tokens):
                if ans == "Yes":
                    ans = "No"
                else:
                    ans = "Yes"

        # case 2: similarity
        sim = fuzz.token_sort_ratio(question, sent)
        if sim > 90:
            ans = "Yes"
        else:
            ans = "No"
        return (ans, sim > self.threshold)

    def qstType(self, qst):
        self.thisType = 'UK'
        self.qstFlag = False
        self.qstSim = None

        tree = self.sNLP.parser_sents([qst, ])
        for i in tree:
            self.decideType(i)
<<<<<<< HEAD
        print(self.thisType)
 
      

=======
>>>>>>> 90a7d73a7620e787ed2b0067d2504ddd436a8ed6

    def fitness(self, txt, qst):
        self.qstType(qst)
        if self.thisType == 'UK':
            _, sim = self.bin_answer(qst, txt)
            return sim

        qstType = self.thisType
        self.candidateAnswer = []
        self.candidateSentence = []

        extendList = []

        for thisSent in [txt]:
            extendList.append(thisSent)
            thisParseTree = self.qgPipeline.getParseTree(thisSent)
            no_conj_list = self.qgPipeline.splitConj(thisParseTree)
            simpl_sents = self.qgPipeline.simplify_sentence(no_conj_list)

            for i in simpl_sents:
                extendList.append(i)
        # pdb.set_trace()

        for txt in extendList:
            # print(txt)
            tree = self.sNLP.parser_sents([txt, ])
            for i in tree:
                self.dropTotal = 0
                self.dropFlag = 1
                while self.dropFlag:
                    self.findFlag = 0
                    nowTree = copy.deepcopy(i)
                    self.dropTime = 0
                    nowTree = self.dropFragment(nowTree, qstType)
                    if self.dropTime <= self.dropTotal:
                        self.dropFlag = 0
                    self.dropTotal += 1

        best_dis = 0
        best_ans = None
        best_candi = None
        best_sen = None

        for i in range(len(self.candidateSentence)):
            nowSentence = ' '.join(self.candidateSentence[i])
            score = fuzz.partial_ratio(self.qstSim, nowSentence)
            this_ans = ' '.join(self.candidateAnswer[i])
            if (score >= best_dis):
                if score == best_dis and len(this_ans) >= len(best_ans):
                    continue
                best_dis = score
                best_sen = nowSentence
                best_ans = this_ans

        return self.threshold < best_dis

    def dropFragment(self, myParent, qstType):
        flag = 0
        for node in myParent:
            if isinstance(node, str): continue
            if self.dropTime > self.dropTotal:
                return
            if node.label() in self.dropType[qstType]:
                self.dropTime += 1
                if self.dropTime > self.dropTotal:
                    myParent.remove(node)
                    self.candidateAnswer.append(node.leaves())
                    self.findFlag = 1
                    return
            self.dropFragment(node, qstType)
            if node.label() == 'ROOT' and self.findFlag:
                # print(node.leaves())
                self.candidateSentence.append(node.leaves())

    def findFragment(self, myParent, qstType):
        for node in myParent:
            if isinstance(node, str): continue
            # node.pretty_print()
            if node.label() in self.dropType[qstType]:
                self.candidateAnswer.append((node.leaves(), node.label()))

            self.findFragment(node, qstType)

    def answerSpecial(self, txtList, tokens, qstType):
        # print(tokens[0])
        self.candidateAnswer = []
        self.finalAnswer = []
        self.candidateSentence = []
        for txt in txtList:
            tree = self.sNLP.parser_sents([txt, ])
            for i in tree:
                self.findFragment(i, qstType)
        for i in self.candidateAnswer:
            sentence = ' '.join(i[0])
            pos_tag = self.sNLP.ner(sentence)
            print(pos_tag)
            # if pos_tag[0][0].lower() not in self.typePro[qstType]:
            #    continue
            if pos_tag[1][1] in self.typeNer[qstType]:
                # print(pos_tag)
                self.finalAnswer.append(sentence)
        print(self.finalAnswer[0])

    def preProcessText(self, text):
        data = re.sub("\(.*\)", "", text)
        data = re.sub(' +', ' ', data).strip()
        return data

    def answer(self, txtList, qst):

        self.qstType(qst)
<<<<<<< HEAD
        self.qstType(qst)
        if self.thisType == 'UK':
            ans, sim = self.bin_answer(qst,txt)
            print(ans)
            return
        #print(self.thisType)
=======
        # print(self.thisType)
>>>>>>> 90a7d73a7620e787ed2b0067d2504ddd436a8ed6

        qstType = self.thisType
        self.candidateAnswer = []
        self.candidateSentence = []

        extendList = []

        for thisSent in txtList:
            thisSent = self.preProcessText(thisSent)
            if (len(word_tokenize(thisSent)) < 4 or len(word_tokenize(thisSent)) > 25):
                continue

            extendList.append(thisSent)
            thisParseTree = self.qgPipeline.getParseTree(thisSent)

            no_conj_list = self.qgPipeline.splitConj(thisParseTree)
            simpl_sents = self.qgPipeline.simplify_sentence(no_conj_list)

            for i in simpl_sents:
                extendList.append(i)
        # pdb.set_trace()

        for txt in extendList:
            # print(txt)
            tree = self.sNLP.parser_sents([txt, ])
            for i in tree:
                self.dropTotal = 0
                self.dropFlag = 1
                while self.dropFlag:
                    self.findFlag = 0
                    nowTree = copy.deepcopy(i)
                    self.dropTime = 0
                    nowTree = self.dropFragment(nowTree, qstType)
                    if self.dropTime <= self.dropTotal:
                        self.dropFlag = 0
                    self.dropTotal += 1

        best_dis = 0
        best_ans = '_'
        best_candi = None
        best_sen = None

        for i in range(len(self.candidateSentence)):
            nowSentence = ' '.join(self.candidateSentence[i])
            # print(nowSentence)
            # print(self.qstSim)
            score = fuzz.partial_ratio(self.qstSim, nowSentence)
            # print(score)
            # print('----------')

            this_ans = ' '.join(self.candidateAnswer[i])
            # print(this_ans, best_ans, score, best_dis)
            if self.qstSim == None: continue
            if this_ans == None: continue
            if (score >= best_dis):
                if score == best_dis and len(this_ans) >= len(best_ans) and self.thisType in ['WHADVP', 'WHPP']:
                    continue
                if score == best_dis and len(this_ans) <= len(best_ans) and self.thisType in ['WHNP']:
                    continue
                best_dis = score
                best_sen = nowSentence
                best_ans = this_ans

        print('++++++++++++++++++')
        print(qst)
        print(best_dis)
        print(best_sen)
        print(best_ans)
        print('++++++++++++++++++')

if __name__ == '__main__':
    QA = QA()

    txt = 'Ram and Raj came to Paris from two provinces in India.'
    qst = 'Where did Ram and Raj came to Paris from?'

    QA = QA.answer(txt, qst)


