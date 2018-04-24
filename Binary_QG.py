#!/usr/bin/env python3

# import these libraries
import re
import sys
import io
import string
import nltk
# from nltk.tag.stanford import StanfordNERTagger
from coreNLP_wrapper import StanfordNLP
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import copy
import What_Who_QG

wnl = WordNetLemmatizer()


def bin_question(sents):
    # preprocessing
    # text_file = sys.argv[1]
    # sentences = []
    # with io.open(text_file, 'r', encoding='utf-8') as f:
    #     for line in f:
    #         line = line.strip()
    #         sentences.extend(sent_tokenize(line))
    # # tagging
    # tokenized_sentences = [word_tokenize(i) for i in sentences if
    #                        (len(word_tokenize(i)) > 5) and (len(word_tokenize(i)) < 25)]

    sNLP = StanfordNLP()

    parse = sNLP.parse(sents)

    sents = What_Who_QG.remove_modifiers(parse)

    # print("remove modifiers", sents)

    tokenized_sentences = []
    tokenized_sentences.append(word_tokenize(sents))

    # print("TOKE", tokenized_sentences)
    aux_words = ['are', 'was', 'were', 'is', 'have', 'has']
    aux_words = set(aux_words)
    question_set = []
    # c = 0
    for sent in tokenized_sentences:
        pos_tags = nltk.pos_tag(sent)
        # print(pos_tags)

        if (pos_tags[0][1] != 'NNP') and (pos_tags[0][1] != 'NNPS'):
            pos_tags[0] = (pos_tags[0][0].lower(), pos_tags[0][1])
        q_list = copy.deepcopy(pos_tags)
        q_string = ''
        for i in range(len(pos_tags)):
            if pos_tags[i][0] in aux_words:
                q_list.insert(0, q_list.pop(i))
                break
            elif pos_tags[i][1] == 'VBD':
                q_list[i] = (wnl.lemmatize(pos_tags[i][0], pos='v'), 'VBD')
                q_list.insert(0, ('Did', 0))
                break
            elif pos_tags[i][1] == 'VBZ':
                q_list[i] = (wnl.lemmatize(pos_tags[i][0], pos='v'), "VBZ")
                q_list.insert(0, ("Does", 0))
                # q_list[i] = wnl.lemmatize(pos_tags[i][0], pos = 'v')
                break
            elif pos_tags[i][1] == 'VBP':
                q_list[i] = (wnl.lemmatize(pos_tags[i][0], pos='v'), "VBP")
                q_list.insert(0, ("Do", 0))
                # q_list[i] = wnl.lemmatize(pos_tags[i][0], pos = 'v')
                break
        if q_list[0][0].lower() in ['are', 'was', 'were', 'is', 'have', 'has', 'did', 'do', 'does']:
            replace_string = q_list[0][0][:1].upper() + q_list[0][0][1:]
            q_list[0] = (replace_string, 0)
            question = ' '.join([i[0] for i in q_list])
            question = question[:-2]
            question = question + "?"

            question_set.append(question)

    # print(question_set)

    return question_set

