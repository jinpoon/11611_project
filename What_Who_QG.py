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
from textblob import Word as wd

# def getNerSet(phrase):
#     sNLP = StanfordNLP()
#     return {t[1] for t in sNLP.ner(phrase)}

# def findMainVerb(dep_tree):
#     for i in dep_tree:
#         if i[1] in ['nsubj', 'csubj', 'nsubjpass']:
#             return(i[0][0], i[0][1])
#     return (None,None)


# def findAuxVerb(dep_tree, verb):
#     aux = ""
#     mod = ""
#     for i in dep_tree:
#         if i[0][0] == verb and i[1] in ["auxpass", "aux"]:
#             aux += i[2][0]+" "
#         if i[0][0] == verb and i[1] in ["adv", "advmod"]:
#             mod += i[2][0] + " "
#     return (aux, mod, verb)

sNLP = StanfordNLP()

def getDecapitalized(sentence):
    tokens = sNLP.word_tokenize(sentence)
    first = tokens[0]
    # print(first)
    thisNER = sNLP.ner(sentence)
    # print(thisNER)
    if thisNER[0][1] not in ['PERSON', 'LOCATION', 'ORGANIZATION', 'CITY', 'NATIONALITY', 'COUNTRY', 'TIME']:
        first = first.lower()
    return first+" "+" ".join(tokens[1:])

def findSubj(dep_list):
    for this in  dep_list:
        if this[1] in ["nsubj", "nsubjpass", "csubj"]:
            return this[2][0]

def findSubjNER(ner, subj):
    for this in ner:
        # print(this)
        if subj == this[0]:
            return this[1]

def getExhaustiveNERs(thisNP):
    word_syns_NER_dict = {}
    for word in word_tokenize(thisNP):
        synonyms = []
        for syn in wn.synsets(word):
            for l in syn.lemmas():
                synonyms.append(l.name())
        word_syns_NER_dict[word] = synonyms

    # print(word_syns_NER_dict)

    for word, values in word_syns_NER_dict.items():
        b = {sNLP.ner(s)[0][1] for s in values}
        word_syns_NER_dict[word] = b

    # print(word_syns_NER_dict)

    for thisWordTag in sNLP.ner(thisNP):
        # print(thisWordTag)
        if thisWordTag[0] in word_syns_NER_dict:
            word_syns_NER_dict[thisWordTag[0]].add(thisWordTag[1])

    set_final_NERs = set()
    for s in word_syns_NER_dict.values():
        set_final_NERs.update(s)

    return (set_final_NERs, word_syns_NER_dict)


def remove_modifiers(parent):
    for node in parent:
        if type(node) is ParentedTree:
            if node.label() == 'ROOT':
                pass
            else:
                if node.label() in ["PP", "ADVP","SBAR"] and node.left_sibling() is None \
                        and node.parent().label() == "S":
                    parent.remove(node)

            if node.parent() is not None:
                remove_modifiers(node)
    str = " ".join(parent.leaves())
    if str.startswith(", "):
        str = str.replace(", ", "", 1)
    return str


def sentence_simplifier(parent, result):
    for node in parent:
        if type(node) is ParentedTree:
            if node.label() == 'ROOT':
                pass
            else:
                if node.label() == "NP" and node.left_sibling() is None \
                        and node.parent().label() == "S" and node.right_sibling() is not None and \
                        node.right_sibling().label() in ["VP","ADVP"]:
                    # print(parent.leaves())
                    if len(parent.leaves()) > 6:
                        if parent.leaves()[-1] == ",":
                            # print(node.leaves()[:-1])
                            p_leaves = parent.leaves()[:-1]
                            p_leaves.append(".")
                            # print(leaves)
                            thisSentence = " ".join(p_leaves)
                        else:
                            p_leaves = parent.leaves()
                            if p_leaves[-1] != ".":
                                p_leaves.append(".")
                            # print(leaves)
                            thisSentence = " ".join(p_leaves)
                        result.append(thisSentence)
            if node.parent() is not None:
                sentence_simplifier(node, result)


def construct_What(question, pos, parent_pos, parent_ner, parent_dep_tree, thisNP):

    prps = ["he", "she", "they", "we", "i"]
    return_Str = ""
    full_NP_ners, word_NP_ners = getExhaustiveNERs(thisNP)
    lower_NP_tokens = thisNP.lower().split(" ")
    # print(lower_NP_tokens)

    subj = findSubj(parent_dep_tree)
    # print("subj", subj)
    subj_ner = findSubjNER(parent_ner, subj)
    # print("subj", subj, "subjNER", subj_ner)

    if pos[0][1] in ["VBD", "VBZ", "NNS", "VBP", "NNP"]:
        # print(full_NP_ners)
        if any(x in lower_NP_tokens for x in prps) or "PERSON" in full_NP_ners or "PERSON" == subj_ner:
            return_Str += "Who "+getDecapitalized(question)
        else:
            return_Str += "What "+getDecapitalized(question)

    elif pos[0][1] in ["VB"]:
        tokens = word_tokenize(getDecapitalized(question))
        # print(tokens,"YOYOYO")
        verb = wd(tokens[0]).pluralize()+" "
        # print(full_NP_ners)
        if verb == "haves": verb = "have"

        if any(x in lower_NP_tokens for x in prps) or "PERSON" in full_NP_ners or "PERSON" == subj_ner:
            return_Str += "Who " + verb + " ".join(tokens[1:])
        else:
            return_Str += "What " + verb + " ".join(tokens[1:])

    elif pos[0][1] in ["VBN", "VBG"]:
        # print(full_NP_ners)
        if any(x in lower_NP_tokens for x in prps) or "PERSON" in full_NP_ners or "PERSON" == subj_ner:
            return_Str += "Who " + getDecapitalized(question)
        else:
            return_Str += "What is " + getDecapitalized(question)


    if return_Str != "":
        return_Str = re.sub(' +', ' ', return_Str).strip()
        que_tokens = word_tokenize(return_Str)
        if que_tokens[-1] == "." or que_tokens[-1] == ",":
            que_tokens[-1] = "?"
        else:
            que_tokens.append("?")
        return " ".join(que_tokens)
    else:
        return None


def what_who_parseTraversal(sent, parent, question):
    thisSent = sent
    for node in parent:
        if type(node) is ParentedTree:
            if node.label() == 'ROOT':
                pass
            else:
                if node.label() == "NP" and node.left_sibling() is None \
                        and node.parent().label() == "S" and node.right_sibling() is not None and \
                            node.right_sibling().label() in ["VP", "ADVP"]:
                    thisNP = " ".join(node.leaves())
                    thisSentence = thisSent.replace(thisNP, "", 1)
                    if thisSentence.startswith(","):
                        thisSentence = thisSentence.replace(", ", "", 1)

                    if len(word_tokenize(thisSentence)) > 7:
                        question.append((thisSentence, thisNP))
                    break

            if node.parent() is not None:  ### recursive to go in depth of the tree
                what_who_parseTraversal(sent, node, question)


def What_Who_module(sent):
    simple_sents = []
    final_ques = []

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

    sents = remove_modifiers(parse)

    parse = sNLP.parse(sents)
    # parse.pretty_print()

    sentence_simplifier(parse, simple_sents)

    # print("1",simple_sents)

    if len(simple_sents) > 1:
        if sent != simple_sents[0]:
            simple_sents = simple_sents[1:]
        # print("2",simple_sents)

    for sentence in simple_sents:
        question = []

        # print("INSIDE FOR LOOP")
        # print(sentence)
        sentence = sentence.replace("/","")
        parse_sent = sNLP.parse(sentence)
        sentence = remove_modifiers(parse_sent)
        # print("removed", sentence)

        parent_dep_tree = sNLP.dependency_parse(sentence)
        parent_dep_tree = parent_dep_tree.__next__()
        p_dep_tree_list = list(parent_dep_tree.triples())

        parse_sent = sNLP.parse(sentence)
        # parse_sent.pretty_print()

        # for t in p_dep_tree_list:
        #     print(t)

        # print(sNLP.ner(sentence))
        # print(sNLP.pos(sentence))

        parent_pos = sNLP.pos(sentence)
        parent_ner = sNLP.ner(sentence)

        what_who_parseTraversal(sentence, parse_sent, question)
        # print("question\n", question)
        for ques, thisNP in question:
            # print(ques)
            # print("inside question for loop...")
            # dep_tree = sNLP.dependency_parse(ques)
            # dep_tree = dep_tree.__next__()
            # dep_tree_list = list(dep_tree.triples())
            # for t in dep_tree_list:
            #     print(t)

            # print(sNLP.pos(ques))
            pos = sNLP.pos(ques)
            # print("FINAL QUESTION")
            thisQ = construct_What(ques, pos, parent_pos, parent_ner, p_dep_tree_list, thisNP)
            # print(thisQ)
            final_ques.append(thisQ)
    # print(final_ques)
    # print()

    return final_ques


    pass