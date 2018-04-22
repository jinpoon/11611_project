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

#os.environ['CLASSPATH'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27'
#os.environ['STANFORD_PARSER'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser.jar'
#os.environ['STANFORD_MODELS'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'
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

    def initQstType(self):
        self.typeSet=['what', 'who', 'which', 'where', 'when']
        self.dropType['who'] = ['NP']
        self.dropType['when'] = ['PP']
        self.dropType['what'] = ['NP']
        self.dropType['where'] = ['PP']
        self.auxWord = ['did','do','does', 'is', 'are','were','was']
        self.typePro['where'] = ['in', 'at', 'on', 'behind', 'next']
        self.typeNer['when'] = ['DATE']
        self.typeNer['where'] = ['CITY','STATE_OR_PROVINCE','ORGANIZATION', 'LOCATION','COUNTRY']


    def qstType(self, qst):
        tokens = self.sNLP.word_tokenize(qst)
        #print(qst, tokens)
        thisType = tokens[0].lower()
        #print(thisType)
    
        if thisType not in self.typeSet: 
            thisType = 'what'#'unknown'
        elif thisType in self.auxWord: 
            thisType = 'binary'


        nextWord = tokens[0]
        backup = tokens
        dropTimes = 0
        while nextWord not in self.auxWord:
            if dropTimes > 3 or dropTimes > len(backup) - 3:
                break
            tokens.pop(0)
            nextWord = tokens[0]
            dropTimes +=1
        
        if dropTimes > 3 or dropTimes > len(backup) - 3:
            tokens = backup
        tokens.pop(0)
        tokens.pop(-1)

        return thisType, tokens



    def dropFragment(self,myParent,qstType):
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
                    self.findFlag  = 1
                    return
            self.dropFragment(node,qstType)
            if node.label() == 'ROOT' and self.findFlag:
                #print(node.leaves())
                self.candidateSentence.append(node.leaves())


    def findFragment(self,myParent,qstType):
        for node in myParent:
            if isinstance(node, str): continue
            #node.pretty_print()
            if node.label() in self.dropType[qstType]:
                self.candidateAnswer.append((node.leaves(), node.label()))
                
            self.findFragment(node,qstType)



    def answerSpecial(self, txtList, tokens, qstType):
        #print(tokens[0])
        self.candidateAnswer = []
        self.finalAnswer = []
        self.candidateSentence = []
        for txt in txtList:
            tree = self.sNLP.parser_sents([txt,])
            for i in tree:
                self.findFragment(i,qstType)
        for i in self.candidateAnswer:
            sentence = ' '.join(i[0])
            pos_tag = self.sNLP.ner(sentence)
            print(pos_tag)
            #if pos_tag[0][0].lower() not in self.typePro[qstType]:
            #    continue
            if pos_tag[1][1] in self.typeNer[qstType]:
                #print(pos_tag)
                self.finalAnswer.append(sentence)
        print(self.finalAnswer[0])



         

    def answer(self, txtList, qst):
        #print('--------')
        #txtList = [txtList[1]]
        #print(txtList)
        #print('--------')
        qstType, tokens = self.qstType(qst)
        if qstType in ['when', 'where']:
            self.answerSpecial(txtList, tokens, qstType)
            return

        self.candidateAnswer = []
        self.candidateSentence = []

        extendList = []

        for thisSent in txtList:
            extendList.append(thisSent)

            thisParseTree = self.qgPipeline.getParseTree(thisSent)
            no_conj_list = self.qgPipeline.splitConj(thisParseTree)            
            simpl_sents = self.qgPipeline.simplify_sentence(no_conj_list)

            for i in simpl_sents:
                extendList.append(i)
        #pdb.set_trace()

        for txt in extendList:
            #print(txt)
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


        best_dis = 999999
        best_ans = None
        best_candi = None

        for i in range(len(self.candidateSentence)):
            nowSentence = self.candidateSentence[i]

            #nowSentence.pop(-1)
            #print(nowSentence, tokens)
            #print(' '.join(nowSentence))
            score = self.edit_distance(nowSentence, tokens)
            best_candi = ' '.join(nowSentence)

            #print(score)
            #print(best_candi)
            if (score < best_dis):
                best_dis = score
                best_ans = ' '.join(self.candidateAnswer[i])
        #print("### sentence is:")
        #print(best_candi)
        #print("### answer is:")
        #print('------------')
        print(best_dis)
        print(best_ans)


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
                insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
                deletions = current_row[j] + 1       # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]


    def give_socre(self, txtList, qst):
        txtList = [txtList]
        qstType, tokens = self.qstType(qst)
        self.candidateAnswer = []
        self.candidateSentence = []
        extendList = []

        for thisSent in txtList:
            extendList.append(thisSent)

            thisParseTree = self.qgPipeline.getParseTree(thisSent)
            no_conj_list = self.qgPipeline.splitConj(thisParseTree)            
            simpl_sents = self.qgPipeline.simplify_sentence(no_conj_list)


            for i in simpl_sents:
                extendList.append(i)
        print(extendList)

        for txt in extendList:
            #print(txt)
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
        best_dis = 999999
        best_ans = None
        best_candi = None

        for i in range(len(self.candidateSentence)):
            nowSentence = self.candidateSentence[i]

            score = self.edit_distance(nowSentence, tokens)
            best_candi = ' '.join(nowSentence)
            if (score < best_dis):
                best_dis = score
                best_ans = ' '.join(self.candidateAnswer[i])
        return best_dis

if __name__ == '__main__':
    QA = QA()

    txt = 'Ram and Raj came to Paris from two provinces in India.'
    qst = 'Where did Ram and Raj came to Paris from?'

    QA =  QA.answer(txt,qst)

  
