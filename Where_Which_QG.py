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
import random

def getNerSet(phrase):
    sNLP = StanfordNLP()
    return {t[1] for t in sNLP.ner(phrase)}

def findMainVerb(dep_tree):
    for i in dep_tree:
        if i[1] in ['nsubj', 'csubj', 'nsubjpass']:
            return(i[0][0], i[0][1])
    return (None,None)


def findAuxVerb(dep_tree, verb):
    aux = ""
    mod = ""
    for i in dep_tree:
        if i[0][0] == verb and i[1] in ["auxpass", "aux"]:
            aux += i[2][0]+" "
        if i[0][0] == verb and i[1] in ["adv", "advmod"]:
            mod += i[2][0] + " "
    return (aux, mod, verb)


def construct_where_which(ques, dep_tree, case, type):

    mVerb, tense = findMainVerb(dep_tree)
    # print(mVerb, tense)
    if mVerb is None or "VB" not in tense:
        return None

    auxVerb, advmod, verb = findAuxVerb(dep_tree, mVerb)
    auxMStr = re.sub(' +',' ',auxVerb+" "+advmod +" "+ verb).strip()
    auxMStr = re.sub(' +', ' ', auxMStr).strip()
    # print(auxVerb, auxMStr)

    thisCase = case.title() if case != "" else "In"
    if auxVerb != "" and auxMStr != "":
        que = ques.replace(auxMStr, mVerb)
        # print(que)
        if random.random() < 0.5:
            que = (thisCase+" which "+type +" "+ auxVerb + " " + que)
        else:
            que = ("Where" + " " + auxVerb + " " + que)
    else:
        tenseVerb = ""
        stemVerb = mVerb
        if tense in ['VBD', 'VBN']:
            tenseVerb = "did"
        elif tense in ['VBZ']:
            tenseVerb = "does"
        # print("mVerb", mVerb)
        stemVerb = WordNetLemmatizer().lemmatize(mVerb,'v')
        # print(stemVerb)

        que = ques.replace(mVerb, stemVerb)
        if random.random() < 0.5:
            que = (thisCase+" which "+ type +" "+ tenseVerb +" "+ que)
        else:
            que = ("Where" +" "+ tenseVerb +" "+ que)

    # print("que", que)
    que_tokens = word_tokenize(que)
    if que_tokens[-1] == "." or que_tokens[-1] == ",":
        que_tokens[-1] = "?"
    else:
        que_tokens.append("?")
    que = " ".join(que_tokens)

    return que

def getWherePhrases(place, dep_tree):
    case = ""
    pos = ""
    det = ""
    compound = ""
    cc = ""
    conj = ""
    amod = ""
    for tuple in dep_tree:
        if tuple[0][0] == place and tuple[1] in ["case"] and tuple[2][1] in ["IN"]:
            case += tuple[2][0] + " "
        if tuple[0][0] == place and tuple[1] in ["det"]:
            det += tuple[2][0] + " "
        if tuple[0][0] == place and tuple[1] in ["case"] and tuple[2][1] in ["POS"]:
            pos += tuple[2][0] + " "
        if tuple[0][0] == place and tuple[1] in ["compound"]:
            compound += tuple[2][0] + " "
        if tuple[0][0] == place and tuple[1] in ["cc"]:
            cc += tuple[2][0] + " "
        if tuple[0][0] == place and tuple[1] in ["conj"]:
            conj += tuple[2][0] + " "
        if tuple[0][0] == place and tuple[1] in ["amod"]:
            amod += tuple[2][0] + " "
    str = case +" "+det+" "+amod+" "+compound+" "+place+" "+pos+" "+cc+" "+conj
    str = re.sub(' +', ' ', str).strip()
    # print("str", str)
    return (str, case)

def where_which_parseTraversal(sent, dep_tree, ner_list, question):
    structure = []
    places = {t[0]:t[1] for t in ner_list if t[1] in ["COUNTRY", "CITY", "LOCATION"]}
    # print(places)

    for t in places:
        str, case = getWherePhrases(t,dep_tree)
        structure.append((str,case,places[t]))
    # print("structure", structure)

    for str, case, type  in structure:
        if case != "":
            # print(str, case, type)
            thisSent = sent.replace(str,"")
            question.append(construct_where_which(thisSent, dep_tree, case, type.lower()))

def where_which_inFirstPP(sent, parent, simple_ques):
    thisSent = sent
    for node in parent:
        if type(node) is ParentedTree:
            if node.label() == 'ROOT':
                pass
            else:
                if (node.label() == "PP" or node.label() == "ADVP") and node.left_sibling() is None:
                    # print("prints")
                    # print(" ".join(node.leaves()))
                    thisPP = " ".join(node.leaves())
                    nerSet = getNerSet(thisPP)
                    # print(nerSet)
                    thisPP = thisPP.replace(" ,", ",").replace(" 's","'s").replace("$ ","$")
                    # print(thisPP)
                    thisSent = thisSent.replace(thisPP, " ").replace(" ,", "")
                    # print(thisSent)
                    if "LOCATION" in nerSet or "CITY" in nerSet or "COUNTRY" in nerSet:
                        simple_ques.append((True, thisSent, nerSet, thisPP))
                    else:
                        simple_ques.append((False, thisSent, nerSet, thisPP))
                    break
            if node.parent() is not None:  ### recursive to go in depth of the tree
                where_which_inFirstPP(sent, node, simple_ques)

def Where_Which_module(sent, sent_features):
    question = []
    simple_ques = []
    sNLP = StanfordNLP()

    # print(sent_features)

    # dep_parse = sNLP.dependency_parse(sent)
    # dep_parse = dep_parse.__next__()
    #
    # dep_parse_list = list(dep_parse.triples())

    parse = sNLP.parse(sent)
    # parse.pretty_print()
    #
    # for t in dep_parse_list:
    #     print(t)

    # print(sNLP.ner(sent))
    # print(sNLP.pos(sent))

    where_which_inFirstPP(sent, parse, simple_ques)
    if len(simple_ques) > 0:
        for bool, thisSent, nerSet, thisPP in simple_ques:
            dep_tree = sNLP.dependency_parse(thisSent)
            dep_tree = dep_tree.__next__()
            dep_tree_list = list(dep_tree.triples())
            # for t in dep_tree_list:
            #     print(t)
            if bool:
                case = thisPP.split(" ")[0]
                type = ""
                if "COUNTRY" in nerSet:
                    type = "country"
                elif "LOCATION" in nerSet:
                    type = "location"
                elif "CITY" in nerSet:
                    type = "city"
                else:
                    type = "place"
                return([construct_where_which(thisSent, dep_tree_list,case,type)])
            else:
                where_which_parseTraversal(thisSent, dep_tree_list, sNLP.ner(thisSent), question)
                return(question)
    else:
        # print("I am in Else")
        thisSent = sent
        dep_tree = sNLP.dependency_parse(thisSent)
        dep_tree = dep_tree.__next__()
        dep_tree_list = list(dep_tree.triples())
        # for t in dep_tree_list:
        #     print(t)
        where_which_parseTraversal(thisSent, dep_tree_list, sNLP.ner(thisSent), question)
        return(question)

    pass