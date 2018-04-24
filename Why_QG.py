#!/usr/bin/env python3

import re
import sys
import io
import string
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import copy
from coreNLP_wrapper import StanfordNLP
import What_Who_QG

wnl = WordNetLemmatizer()

why_keys = ['because', 'as a result', 'due to', 'in order to']
why_keys = set(why_keys)

aux_words = ['are', 'was', 'were', 'is', 'have', 'has']
aux_words = set(aux_words)


def why_q(sents):
    # preprocessing

    sNLP = StanfordNLP()

    parse = sNLP.parse(sents)

    sents = What_Who_QG.remove_modifiers(parse)

    # print("remove modifiers", sents)

    tokenized_sentences = []
    question = ""

    tokenized_sentences.append(word_tokenize(sents))
    q_set = []
    for sent in tokenized_sentences:
        pos_tags = nltk.pos_tag(sent)
        # print(pos_tags)
        if (pos_tags[0][1] != 'NNP') and (pos_tags[0][1] != 'NNPS'):
            pos_tags[0] = (pos_tags[0][0].lower(), pos_tags[0][1])
        q_list = copy.deepcopy(pos_tags)
        q_string = ''
        #print(pos_tags)

        for i in range(len(pos_tags)):
            if pos_tags[i][1] == 'VBD':
                q_list[i] = (wnl.lemmatize(pos_tags[i][0], pos = 'v'), 'VBD')
                q_list.insert(0, ('Why did', 0))
                break
            elif pos_tags[i][1] == 'VBZ':
                if pos_tags[i][0] in aux_words:
                    q_list.insert(0, q_list.pop(i))
                    q_list.insert(0, ("Why", 0))
                else:
                    q_list[i] = (wnl.lemmatize(pos_tags[i][0], pos = 'v'), "VBZ")
                    if q_list[i][0] == "do": q_list.pop(i)
                    q_list.insert(0, ("Why does", 0))
                break
            elif pos_tags[i][1] == 'VBP':
                q_list.insert(0, q_list.pop(i))
                q_list.insert(0, ("Why", 0))
                break
        replace_string = q_list[0][0][:1].upper() + q_list[0][0][1:]
        q_list[0] = (replace_string, 0)
        #print(q_list)

        question = ' '.join([i[0] for i in q_list])
        ind = -1
        for k in why_keys:
            if question.find(k) != -1:
                ind = question.find(k)
                break
        if ind != -1:
            question = question[:ind-1]
        question = question + "?"
        # print(question)

    if question != "":
        return (question)
    else:
        return None



