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
from What_Who_QG import getDecapitalized

def getNerSet(phrase):
    sNLP = StanfordNLP()
    return {t[1] for t in sNLP.ner(phrase)}

def findMainVerb(dep_tree):
    for i in dep_tree:
        if i[1] in ['nsubj', 'csubj', 'nsubjpass']:
            return(i[0][0], i[0][1])
    return (None,None)

def findAuxVerb(dep_tree, verb):
    for i in dep_tree:
        if i[0][0] == verb and i[1] in ["auxpass", "aux"]:
            return (i[2][0], i[2][0] + " " + i[0][0])
    return (None, None)

def construct_when(ques, dep_tree):

    mVerb, tense = findMainVerb(dep_tree)
    # print(mVerb, tense)
    if mVerb is None or "VB" not in tense:
        return None

    auxVerb, auxMStr = findAuxVerb(dep_tree, mVerb)
    # print(auxVerb, auxMStr)
    if auxVerb is not None and auxMStr is not None:
        que = ques.replace(auxMStr, mVerb)
        # print(que)
        que = ("When "+ auxVerb + " " + getDecapitalized(que))
    else:
        tenseVerb = ""
        stemVerb = mVerb
        if tense in ['VBD', 'VBN']:
            tenseVerb = "did"
        elif tense in ['VBZ']:
            tenseVerb = "does"
        stemVerb = WordNetLemmatizer().lemmatize(mVerb,'v')

        que = ques.replace(mVerb, stemVerb)
        que = ("When " + tenseVerb +" "+ getDecapitalized(que))
        # print("que", que)
    que_tokens = word_tokenize(que)
    if que_tokens[-1] == "." or que_tokens[-1] == ",":
        que_tokens[-1] = "?"
    else:
        que_tokens.append("?")
    que = " ".join(que_tokens)

    return que

def when_parseTraversal(sent, parent, question, structures):
    thisSent = sent
    for node in parent:
        if type(node) is ParentedTree:
            if node.label() == 'ROOT':
                pass
            else:
                if (node.label() == "PP" or node.label() == "NP-TMP") and node.left_sibling() is None:
                    thisPP = " ".join(node.leaves())
                    nerSet = getNerSet(thisPP)
                    if "DATE" in nerSet or "TIME" in nerSet:
                        # thisPP = thisPP + ", "
                        thisPP = thisPP.replace(" ,", ",")
                        # print(thisPP)
                        thisSentence = thisSent.replace(thisPP, "").replace(", ","")
                        question.append(thisSentence)
                    break
                if node.label() == "PP":
                    this = " ".join(node.leaves())
                    this = this.replace(" ,", ",")
                    nerSet = getNerSet(this)
                    if "DATE" in nerSet or "TIME" in nerSet:
                        structures.append((this, len(this)))


            if node.parent() is not None:  ### recursive to go in depth of the tree
                when_parseTraversal(sent, node, question, structures)


def When_module(sent, sent_features):
    question = []
    structures = []
    sNLP = StanfordNLP()

    # print(sent_features)

    # dep_parse = sNLP.dependency_parse(sent)
    # dep_parse = dep_parse.__next__()
    #
    # dep_parse_list = list(dep_parse.triples())

    parse = sNLP.parse(sent)
    # parse.pretty_print()

    # for t in dep_parse_list:
    #     print(t)

    # print(sNLP.ner(sent))
    # print(sNLP.pos(sent))

    when_parseTraversal(sent, parse, question, structures)
    # print(question)
    # print(structures)
    prev_min = float('Inf')

    if len(structures) > 0:
        whenPhrase = ""
        for t in structures:
            if t[1] < prev_min:
                whenPhrase = t[0]
                prev_min = t[1]
        # print(sent)
        # print(whenPhrase)
        thisQ = sent.replace(whenPhrase, "")
        dep_tree = sNLP.dependency_parse(thisQ)
        dep_tree = dep_tree.__next__()
        dep_tree_list = list(dep_tree.triples())
        # for t in dep_tree_list:
        #     print(t)
        return construct_when(thisQ, dep_tree_list)

    for q in question:
        dep_tree = sNLP.dependency_parse(q)
        dep_tree = dep_tree.__next__()
        dep_tree_list = list(dep_tree.triples())
        # for t in dep_tree_list:
        #     print(t)
        return construct_when(q,dep_tree_list)

    # print()


    pass
