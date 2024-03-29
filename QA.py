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
from nltk.stem.wordnet import WordNetLemmatizer
from What_Who_QG import *
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
            #node.pretty_print()
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

    def parseDep(self, x):
        a = x[0][0].lower()
        a = WordNetLemmatizer().lemmatize(a)
        b = x[2][0].lower()
        b = WordNetLemmatizer().lemmatize(b)
        return (a, b)

    def bin_answer(self, question, sent):
        #print(question, sent)

        qstTree = self.sNLP.dependency_parse(question)
        qstTree = qstTree.__next__()
        qstTree = list(qstTree.triples())
        sentTree = self.sNLP.dependency_parse(sent)
        sentTree = sentTree.__next__()
        sentTree = list(sentTree.triples())
        #print(qstTree, sentTree)
        qstSub = []
        sentSub = []
        flag = False
        neg = False
        for x in qstTree:
            # print(x)
            if x[1] in ['nsubj', 'nsubjpass', 'csubj', 'csubjpass']:
                qstSub.append(self.parseDep(x))
            if x[1] == 'neg':
                neg = True
        for x in sentTree:
            if x[1] in ['nsubj', 'nsubjpass', 'csubj', 'csubjpass']:
                sentSub.append(self.parseDep(x))
                if self.parseDep(x) in qstSub:
                    flag = True
        #print(qstSub)
        #print(sentSub)

        if flag:
            if neg:
                return ('No', 100)
            else:
                return ('Yes', 100)

        bin_tags = set(["did", 'do', 'does', 'are', 'is', 'have', 'was',
                        'were', 'has'])
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
        sim = fuzz.partial_ratio(question, sent)
        if sim > 90:
            ans = "Yes"
        else:
            ans = "No"
        return (ans, sim)

    def qstType(self, qst):
        self.thisType = 'UK'
        self.qstFlag = False
        self.qstSim = None

        tree = self.sNLP.parser_sents([qst, ])
        for i in tree:
            self.decideType(i)

    def fitness(self, txt, qst):
        self.qstType(qst)
        if self.thisType == 'UK':
            _, sim = self.bin_answer(qst, txt)
            return sim > self.threshold
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
        best_ans = '_'
        best_candi = None
        best_sen = None

        for i in range(len(self.candidateSentence)):
            nowSentence = ' '.join(self.candidateSentence[i])
            score = fuzz.partial_ratio(self.qstSim, nowSentence)
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
            if pos_tag[1][1] in self.typeNer[qstType]:
                # print(pos_tag)
                self.finalAnswer.append(sentence)
        print(self.finalAnswer[0])

    def preProcessText(self, text):
        data = re.sub("\(.*\)", "", text)
        data = re.sub(' +', ' ', data).strip()
        return data

    def answer(self, txtList, qst):
        self.head = word_tokenize(qst)[0].lower()


        self.qstType(qst)
        if self.thisType == 'UK':

            best_score = 0
            best_ans = 'Yes'
            best_sent = '_'
            for txt in txtList:
                ans, sim = self.bin_answer(qst, txt)
                if sim > best_score:
                    best_ans = ans
                    best_score = sim
                    best_sent = txt
            #print('=======')
            #print(best_sent)
            #print(qst)
            print(best_ans+'.')
            #print(best_score)
            #print('=======')
            return

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
        best_candi = None
        best_sen = None
        best_ans = '_'

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
                if self.head=='who':
                    ners = getExhaustiveNERs(this_ans)
                    #print(this_ans, ners[0])
                    if  'PERSON' not in ners[0] and 'ORGANIZATION' not in ners[0]: 
                        if score - best_dis < 10:
                            continue
                        else:
                            score = score - 10
                if self.head=='when':
                    ners = getExhaustiveNERs(this_ans)
                    if 'DATE' not in ners[0]: 
                        if score - best_dis < 10:
                            continue
                        else:
                            score = score - 10
                if self.head=='where':
                    ners = getExhaustiveNERs(this_ans)
                    if 'LOCATION' not in ners[0] and 'CITY' not in ners[0] and 'ORGANIZATION' not in ners[0] and 'STATE_OR_PROVINCE' not in ners[0] and 'COUNTRY' not in ners[0]: 
                        if score - best_dis < 10:
                            continue
                        else:
                            score = score - 10
                best_dis = score

                best_sen = nowSentence
                best_ans = this_ans

        #print('++++++++++++++++++')
        #print(qst)
        #print(best_dis)
        #print(best_sen)
        if best_ans == '_':
            print('I cannot answer that question: '+qst)
        else :
            print(best_ans.capitalize()+'.')
        #print('++++++++++++++++++')

    def edit_distance(self, s1, s2):
        if len(s1) < len(s2):
            return self.edit_distance(s2, s1)
        # len(s1) >= len(s2)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            c1 = c1.lower()
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                c2 = c2.lower()
                insertions = previous_row[
                                 j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
                deletions = current_row[j] + 1  # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

        for i in range(len(self.candidateSentence)):
            nowSentence = self.candidateSentence[i]

            score = self.edit_distance(nowSentence, tokens)
            best_candi = ' '.join(nowSentence)
            this_ans = ' '.join(self.candidateAnswer[i])
            if (score < best_dis or (score == best_dis and len(this_ans) < len(best_ans))):
                best_dis = score
                best_ans = this_ans
        return best_dis


if __name__ == '__main__':
    QA = QA()

    txt = 'Ram and Raj came to Paris from two provinces in India.'
    qst = 'Where did Ram and Raj came to Paris from?'

    QA = QA.answer(txt, qst)


