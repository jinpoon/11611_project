import re
import os
import requests
from nltk.parse import stanford
from nltk.tokenize import word_tokenize
from collections import defaultdict
import json
from nltk.tree import *
import string
import nltk
import sys
from testscript import *
from coreNLP_wrapper import StanfordNLP
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
import string
from nltk.corpus import wordnet as wn
from nltk.stem import *
from nltk.stem.wordnet import WordNetLemmatizer
import When_QG
import Where_Which_QG
import What_Who_QG
import Binary_QG
import Why_QG
from QA import QA
from testscript import *


aux_words = ['are', 'was', 'were', 'is', 'have', 'has']
aux_words = set(aux_words)

why_keys = ['because', 'as a result', 'due to', 'in order to']
why_keys = set(why_keys)

def categorizeQs(sents, sent_to_Q_dict):
    # print(sents)
    sent_features = {}
    sNLP = StanfordNLP()
    normal_ners = sNLP.ner(sents)
    normal_ner_set = {t[1] for t in normal_ners}

    aux_Flag = max([1 if w in sents else 0 for w in aux_words])
    # print(aux_Flag)
    if aux_Flag == 1:
        thisQues = Binary_QG.bin_question(sents)
        for p_b in thisQues:
            if p_b is not None:
                sent_to_Q_dict["Binary"].append((sents,p_b))

    why_flag = max([1 if w in sents else 0 for w in why_keys])
    # print(why_flag)
    if why_flag == 1:
        thisQues = Why_QG.why_q(sents)
        if thisQues is not None:
                sent_to_Q_dict["Why"].append((sents,thisQues))

    thisQues = What_Who_QG.What_Who_module(sents)
    for p_ in thisQues:
        if p_ is not None:
            sent_to_Q_dict["What_Who"].append((sents,p_))

    if 'LOCATION' in normal_ner_set or 'COUNTRY' in normal_ner_set or 'CITY' in normal_ner_set:
        thisQ = Where_Which_QG.Where_Which_module(sents, sent_features)
        for p in thisQ:
            if p is not None:
                sent_to_Q_dict["Where_Which"].append((sents,p))

    if 'DATE' in normal_ner_set or 'TIME' in normal_ner_set:
        thisQ = When_QG.When_module(sents,sent_features)
        if thisQ is not None:
            sent_to_Q_dict["When"].append((sents,thisQ))


def SentToQuesBuckets(sent_list):
    sent_to_Q_dict = {}
    sent_to_Q_dict["When"] = []
    sent_to_Q_dict["What_Who"] = []
    sent_to_Q_dict["Why"] = []
    sent_to_Q_dict["How"] = []
    sent_to_Q_dict["Where_Which"] = []
    sent_to_Q_dict["Binary"] = []

    for sents in sent_list:

        sents = re.sub("\(.*\)", "", sents)
        sents = re.sub("\[.*\]", "", sents)
        sents = sents.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace('"', "")
        # print(sents)
        sents = re.sub(' +', ' ', sents).strip()

        if len(word_tokenize(sents)) > 6 and len(word_tokenize(sents)) < 25 \
                    and word_tokenize(sents)[-1] in string.punctuation:
            if sents != "":
                categorizeQs(sents, sent_to_Q_dict)


    return sent_to_Q_dict



def askMe(sents):

    final_sents = sents[:]
    # print(final_sents)
    result = []
    bucks = SentToQuesBuckets(final_sents)
    for b in bucks:
        result.extend(bucks[b])
        # for b_ in bucks[b]:
            # print(b_)

    ##### Question ranking

    evaluator = QuestionEvaluator(productions_filename = "questionbank_pcfg.txt")

    evaluations =[(evaluator.evaluate(i[1]), i) for i in result if (len(word_tokenize(i[1]))-1) > 5]
    evaluations = sorted(evaluations)
    evaluations = evaluations[::-1]
    # print("+++++++++++++++++++++++++ Answering Interface ++++++++++++++++++++++++++++++++++")
    #
    # new_evaluation = []
    # for this in evaluations:
    #     print(this[1][0],this[1][1])
    #     if qa.fitness(this[1][0],this[1][1]):
    #         new_evaluation.append(this[1][1])
    #
    # # new_evaluation = [this[1][1] for this in evaluations if QA.fitness(this[1][0],this[1][1])]
    #
    # ctr = 0
    # for this in new_evaluation:
    #     ctr += 1
    #     print(this)
    #     # if ctr < n:
    #     #     break
    #
    # print("+++++++++++++++++++++++++ Answering Interface ++++++++++++++++++++++++++++++++++")

    return evaluations

