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

#os.environ['CLASSPATH'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27'
#os.environ['STANFORD_PARSER'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser.jar'
#os.environ['STANFORD_MODELS'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'

#os.environ['CLASSPATH'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/jars'
#os.environ['STANFORD_MODELS'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/models'




class Simplification:
    ##### Split on conjunctions and some more simplifications in the complex parent sentence

    def __init__(self):
        self.sNLP = StanfordNLP()

    def coref_resolve(self, passage):
        text = "John is a tennis player. He has an awesome physique."
        result = json.loads(self.sNLP.coref(text))
        # print()
        # print(result['sentences'])
        num, mentions = list(result['corefs'].items())[0]

    def splitConjunctions(self, parent, list_sents, firstPP):
        firstFlag = 0
        for node in parent:
            if type(node) is ParentedTree:
                if node.label() == 'ROOT':
                    pass
                else:
                    # print("Label:", node.label())
                    # print("Leaves:", node.leaves())
                    # print("Parent:", node.parent().label())
                    # print(node.left_sibling())
                    # print(node.label())
                    # print(node.right_sibling())
                    # print(node.parent().label())
                    # print(len(node))

                    # if the starting of the sentence is with a Prepositional phrase move it to the last child of each verb phrase seen
                    if node.label() == "PP" and node.parent().label() == "S" and node.left_sibling() is None:
                        parent.remove(node)
                        firstPP = node  # make a copy
                        firstFlag = 1
                        # print("firstPP parent", firstPP.parent())
                        # print(firstPP)
                    # for each  VP insert the extracted PP as the last child

                    elif node.label() == "VP" and firstPP is not None and node.parent().label() == 'S':
                        # print("Im inside firstPP")
                        # node.pretty_print()
                        # firstPP.pretty_print()
                        # print(firstPP.parent())
                        # if node.right_sibling().label() == '.' or node.right_sibling().label() == 'CC':
                        node.insert(len(node), firstPP)
                        # node.pretty_print()

                    #### split on conjunctions iff left and right siblings of CC except (or, nor) are S
                    if node.label() == "CC" and node.leaves() not in ('or', 'Or', 'nor', 'Nor') and \
                            node.left_sibling() is not None and node.right_sibling() is not None:
                        # print("Im here")
                        # print(node.left_sibling().label())
                        # print(node.right_sibling().label())
                        if node.left_sibling().label() == "S":
                            list_sents.append(node.left_sibling())
                        if node.right_sibling().label() == "S":
                            list_sents.append(node.right_sibling())

                if node.parent() is not None:
                    if firstFlag:
                        firstPP_temp = firstPP.copy(
                            deep=True)  # maintain a copy of the first PP found through out the recursion
                    else:
                        firstPP_temp = None
                    self.splitConjunctions(node, list_sents, firstPP_temp)
        return list_sents

    ####### traverse and simplify sentence

    def traversalAndSimplification(self, parent):
        for node in parent:
            if type(node) is ParentedTree:
                # node.pretty_print()
                # print("here", )
                # print(len(node))
                # print("in the loop", node.leaves())
                if node.label() == 'ROOT':
                    pass
                else:
                    # print("Label:", node.label())
                    # print("Leaves:", node.leaves())
                    # print("Parent:", node.parent().label())

                    ###### if Adverbial or relative clause or modifiers in a sentence remove them
                    if node.label() in ("ADVP", "SBAR", "SBARQ"):
                        # node.pretty_print()
                        # print(parent.leaves())
                        parent.remove(node)

                        # print(parent.leaves())

                    ###### if VP node has a child PP as the last child preceeeding by a comma remove it
                    elif node.label() == 'PP' and node.parent().label() == "VP" and node.left_sibling().label() == ',':
                        parent.remove(node)
                        # print(parent.leaves())

                    ###### if a NP has modifiers offset by commas remove it
                    elif node.parent().label() == 'NP' and node.left_sibling() is not None and node.right_sibling() is not None:
                        if node.left_sibling().label() == ',' and node.right_sibling().label() == ',':
                            # print("lefty: here I am")
                            # node.pretty_print()
                            # print(parent.leaves())
                            parent.remove(node)
                            # print(parent.leaves())

                if node.parent() is not None:  ### recursive to go in depth of the tree
                    self.traversalAndSimplification(node)
            # else:
            # print("Word:", node)pass
        return (parent.leaves())


###### Method to generate questions
class QuestionGeneration:

    def __init__(self):
        self.sNLP = StanfordNLP()
        self.beVerbs = {"am", "is", "are", "was", "were"}
        # self.aux_verbs = {'is', 'were', 'can', 'could', }

    def auxilaryWord(self, sub, POS_tag):
        # TODO lowercase
        # TODO will may...
        # TODO plural...
        # Jerry and I
        if sub.lower() in ('i', 'they', 'you'):
            return 'do'
        if sub.lower() in ('he', 'she'):
            return 'does'

    def beWork(self, sentence):
        # pos = nltk.pos_tag(sentence)
        j = None
        for i in range(len(sentence) - 1):
            if sentence[i] in self.beVerbs:
                j = i
                break
        if j is not None:
            temp = sentence[j]
            sentence.pop(j)
            sentence.insert(0, temp)
            #print(sentence)
            return sentence

        return

    # def getNounandVerbOfSentence(self, sentence):

    def QG(self, text):

        # create a parse tree
        # parseTree = sNLP.parse(text)
        # print(parseTree)

        # create a DEPENDENCY PARSE tree to understand the relation from the main verb
        dep_parse_Tree = self.sNLP.dependency_parse(text)
        dep_parse_Tree = dep_parse_Tree.__next__()
        Ques_list = []

        # Yes or No question

        be_question = self.beWork(text)
        if be_question is not None:
            be_question += '?'
            Ques_list.append(be_question)

        # WHO question for Subject

        # create NER tags
        ner_tags = dict(self.sNLP.ner(text))
        pos_tag = self.sNLP.pos(text)
        #print(ner_tags)

        # get triples list of the dependency tree
        triples_list = list(dep_parse_Tree.triples())
        #print(triples_list)
        ##### LOOP THRU DEPENDENCY TREE AND CREATE QUESTIONS
        auxWord = 'xxx'
        for this in triples_list:
            # print(this)
            temp_text = '?'

            # for the subject question
            if this[1] in ['nsubj', 'csubj', 'nsubjpass']:
                subject = None
                sub_pos = None
                # in order of preference
                if this[2][1] in ['NNP', 'NNPS', 'PRP']:
                    subject = this[2][0]
                    sub_pos = this[2][1]
                elif this[0][1] in ['NNP', 'NNPS']:
                    subject = this[0][0]
                    sub_pos = this[0][1]
                elif this[2][1] in ['NN', 'NNS']:
                    subject = this[2][0]
                    sub_pos = this[2][1]


                #print("sub", subject)
                if subject is not None:  # need to add sub_pos
                    auxWord = self.auxilaryWord(subject, sub_pos)

                    if ner_tags[subject] in ['PERSON', 'TITLE', 'MISC']:  # check if its a PERSON NER
                        temp_text = self.contructQ(triples_list, subject, text, None)
                        temp_text = temp_text.replace(subject, "Who").replace(" .", "?")  # create question

                        # some string manipulation to get the ?
                        if "?" not in temp_text:
                            temp_text = temp_text + "?"
                            # print(text.replace(subject, "Who").replace(" .", "?"))

                    if ner_tags[subject] == 'ORGANIZATION':  # if the subject is ORG
                        temp_text = text.replace(subject, "Which organization").replace(" .", "?")

                    if ner_tags[subject] == 'CITY':  # if the subject is CITY
                        temp_text = text.replace(subject, "Which city").replace(" .", "?")

                    if ner_tags[subject] == 'COUNTRY':  # if the subject is CITY
                        temp_text = text.replace(subject, "Which country").replace(" .", "?")

                    if this[2][1] in ['PRP']:  # if the subject is preposition
                        temp_text = text.replace(subject, "Who").replace(" .", "?")

                    if ner_tags[subject] in ['O', 'LOCATION'] and temp_text == '?':  # if the subject is Other
                        temp_text = self.contructQ(triples_list, subject, text, None)
                        if sub_pos == 'PRP' and subject.lower() in ['they', 'he', 'she']:
                            temp_text = temp_text.replace(subject, "Who").replace(" .", "?")
                        else:
                            temp_text = temp_text.replace(subject, "What").replace(" .", "?")

            # for number, How many questions
            elif this[1] in ['nummod']:
                numPhrase = this[2][0] + ' ' + this[0][0]
                targetWord = this[2][0]
                if ner_tags[targetWord] in ('NUMBERS'):
                    temp_text = text.replace(numPhrase, "").replace(" .", "?")
                    temp_text = "How many " + this[0][0] + " " + (
                    auxWord if auxWord is not None else "") + " " + temp_text

            # for possessive questions
            elif this[1] in ['nmod:poss']:
                if this[2][1] in ['NNP']:
                    # if this[2][0][-1] == 's':
                    #     poss_word = this[2][0]
                    # else:
                    poss_word = this[2][0] #+ " 's"
                    temp_text = self.contructQ(triples_list, this[2][0], text, None)
                    temp_text = temp_text.replace(poss_word, "Whose").replace(" .", "?").replace("'s", "").replace(" '","")
                    if not temp_text.startswith("Whose"):
                        temp_text = temp_text.replace("Whose", "whose").replace(" '", "")


            # for prop questions
            elif this[1] in ('case'):
                subject = this[0][0]
                propPhrase = this[2][0] + ' ' + this[0][0]
                # print(propPhrase)
                if ner_tags[subject] in ['CITY']:  # where
                    temp_text = text.replace(propPhrase, "").replace(" .", "?")  # create question
                    temp_text = "Where " + (auxWord if auxWord is not None else "") + " " + temp_text
                    # some string manipulation to get the ?
                if ner_tags[subject] in ['DATE']:  # when
                    temp_text = text.replace(propPhrase, "").replace(" .", "?")
                    # print(auxWord, temp_text)
                    temp_text = "When " + (auxWord if auxWord is not None else "") + " " + temp_text

            elif this[1] in ('iobj', 'dobj'):
                # code to be written for questions on direct and indirect Objects
                pass
            #### endif

            if "?" not in temp_text:
                temp_text = temp_text + "?"
            if temp_text != '?':
                # print(temp_text)
                Ques_list.append(temp_text)

        return (Ques_list)

    #### in case of the subject has modifiers or the Subject is a part of a long NP remove all the related modifiers of the subject with the help of dependency tree
    #### same to be replicated for Object as well
    def contructQ(self, list_triples, subject, text, object):

        if subject is not None:
            text = text[text.find(subject):]  ## removing unnecessary determinants (a, the, An) by slicing off until the subject word
            # print(text)
            dict_of_words_removed = {}  # subject related word removal to construct a question
            for thisTriple in list_triples:  ## loop thru dependency tree
                if thisTriple[0][0] == subject or thisTriple[0][0] in dict_of_words_removed:
                    if thisTriple[1] not in ['nsubj', 'csubj']:
                        if (thisTriple[2][0]).lower() not in ['the', 'a',
                                                              'an']:  # skipping determinants as they can be present in other places of the sentence as well
                            text = re.sub(' +', ' ',
                                          text.replace(thisTriple[2][0], '')).strip()  # removing subject related words
                            dict_of_words_removed[thisTriple[2][
                                0]] = 0  # adding the removed word so that other words that are connected to this can also be removed
       
        return (text)

class QGPipeline:

    # SENTENCE SIMPLIFICATION
    ### removing parenthetical phrases
    # print(text)
    def __init__(self):
        self.sNLP = StanfordNLP()
        self.sent_simpl = Simplification()
        self.QG = QuestionGeneration()

    def getParseTree(self, text):
        # text = re.sub("\(.*\)", "", text)
        # text = re.sub("\\n", "", text)
        t = self.sNLP.parse(text)
        # print("Parse:", t)
        return (t)

    def splitConj(self, t):
        # STEP 1: split on conjunctions
        t_list = []
        t_list = self.sent_simpl.splitConjunctions(t, t_list, None)

        if len(t_list) == 0:
            t_list.append(t)

        return (t_list)

    # Simplify split parent sentences
    def simplify_sentence(self, t_list):
        simplified_sentences = []
        for this in t_list:
            processed_text = " ".join(self.sent_simpl.traversalAndSimplification(this))
            processed_text = processed_text.replace(",", "")
            processed_text = re.sub(' +', ' ', processed_text).strip()
            if processed_text[-1] != '.':
                processed_text += ' .'
            simplified_sentences.append(processed_text)

        return (simplified_sentences)

    # print("Simplified Sentences...")
    # print(simplified_sentences)

    #### Question generation
    def QuesGen(self, simplified_sentences):
        final_q_list = []

        for this in simplified_sentences:
            final_q_list.extend(self.QG.QG(this))
        # print("Questions...")
        return (final_q_list)
    # print(final_q_list)


class TextManipulator():

    def __init__(self, dataFile):
        self.sNLP = StanfordNLP()
        self.punc = {'.', '?', '!', '\n'}
        # self.textData = open(dataFile,"r", encoding='utf-8').read()
        self.textData = dataFile
        self.textData = self.preProcessText(self.textData)
        self.sentence_list = []
        # self.getSentenceList(self.textData)
        self.tokenizePara(self.textData)

    def preProcessText(self, text):
        data = re.sub("\(.*\)", "", text)
        data = re.sub(' +', ' ', data).strip()
        return data

    def tokenizePara(self, textCorpus):
        Tokens = word_tokenize(textCorpus)
        sentence = []
        for i in range(len(Tokens)):
            sentence.append(Tokens[i])
            if Tokens[i] in {'.', ';', '!'}:
                self.sentence_list.append(' '.join(sentence))
                sentence = []
        pass

class QG:
    def __init__(self, text):
        self.proper = 1
        count = len(word_tokenize(text))
        if count > 20:
            self.proper = 0
            return
        textManipulation = TextManipulator(text)
        list_sents = textManipulation.sentence_list
        ### NEED TO DO COREFERENCE HERE

        #creating the questions generation engine
        qgPipeline = QGPipeline()

        self.final_Ques = []
        for thisSent in list_sents:
            # get parse tree
            thisParseTree = qgPipeline.getParseTree(thisSent)
            # print(thisParseTree)
            #thisParseTree.pretty_print()
            # separate conjun based questions
            no_conj_list = qgPipeline.splitConj(thisParseTree)
            # print(no_conj_list)
            # simplify sentences
            simpl_sents = qgPipeline.simplify_sentence(no_conj_list)
            # print(simpl_sents)
            # question collection
            self.final_Ques.extend(qgPipeline.QuesGen(simpl_sents))
            # print(final_Ques)


    def run(self,n):
        if not self.proper: 
            return []
        evaluator = QuestionEvaluator(productions_filename = "questionbank_pcfg.txt")

        evaluations =[(evaluator.evaluate(i), i) for i in self.final_Ques]
        evaluations = sorted(evaluations)
        #return_list = []
        return evaluations[:n]



'''
#TODO extractHelper
#TODO Decomposition of the Main Verb
#TODO passive voice
#TODO coreference
'''
