
import re
import os
from nltk.parse import stanford
from collections import defaultdict
from stanfordcorenlp import StanfordCoreNLP
import json
from nltk.tree import *
import string

os.environ['CLASSPATH'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/jars'
os.environ['STANFORD_MODELS'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/models'


class StanfordNLP:
    def __init__(self, host='http://localhost', port=9000):
        self.nlp = StanfordCoreNLP(host, port=port,
                                   timeout=30000)  # , quiet=False, logging_level=logging.DEBUG)
        self.nlp_depParser = stanford.StanfordDependencyParser()

        self.props = {
            'annotators': 'coref',
            'pipelineLanguage': 'en',
            'outputFormat': 'json'
        }

    def word_tokenize(self, sentence):
        return self.nlp.word_tokenize(sentence)

    def pos(self, sentence):
        return self.nlp.pos_tag(sentence)

    def ner(self, sentence):
        return self.nlp.ner(sentence)

    def parse(self, sentence):
        return ParentedTree.convert(Tree.fromstring(self.nlp.parse(sentence)))

    # def dependency_parse(self, sentence):
    #     return self.nlp.dependency_parse(sentence)
    def dependency_parse(self, sentence):
        return self.nlp_depParser.raw_parse(sentence)

    def annotate(self, sentence):
        return json.loads(self.nlp.annotate(sentence, properties=self.props))

    @staticmethod
    def tokens_to_dict(_tokens):
        tokens = defaultdict(dict)
        for token in _tokens:
            tokens[int(token['index'])] = {
                'word': token['word'],
                'lemma': token['lemma'],
                'pos': token['pos'],
                'ner': token['ner']
            }
        return tokens

##### Split on conjunctions and some more simplifications in the complex parent sentence
def splitConjunctions(parent, list_sents, firstPP):
    for node in parent:
        if type(node) is ParentedTree:
            if node.label() == 'ROOT':
                print("======== Sentence =========")
                print("Sentence:", " ".join(node.leaves()))
            else:
                # print("Label:", node.label())
                # print("Leaves:", node.leaves())
                # print("Parent:", node.parent().label())

                # if the starting of the sentence is with a Prepositional phrase move it to the last child of each verb phrase seen
                if node.label() == "PP" and node.parent().label() == "S" and node.left_sibling() is None:
                    parent.remove(node)
                    firstPP = node # make a copy
                    # print("firstPP parent", firstPP.parent())
                    # print(firstPP)
                # for each  VP insert the extracted PP as the last child
                elif node.label() == "VP" and firstPP is not None:
                    # print("Im inside firstPP")
                    # node.pretty_print()
                    # firstPP.pretty_print()
                    # print(firstPP.parent())
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
                if firstPP is not None:
                    firstPP_temp = firstPP.copy(deep=True) # maintain a copy of the first PP found through out the recursion
                else:
                    firstPP_temp = None
                splitConjunctions(node, list_sents, firstPP_temp)

    return list_sents


####### traverse and simplify sentence

def getNodes(parent):
    for node in parent:
        if type(node) is ParentedTree:
            # node.pretty_print()
            # print("here", )
            # print(len(node))
            # print("in the loop", node.leaves())
            if node.label() == 'ROOT':
                print("======== Sentence =========")
                print("Sentence:", " ".join(node.leaves()))
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


            if node.parent() is not None: ### recursive to go in depth of the tree
                getNodes(node)
        # else:
            # print("Word:", node)pass
    return (parent.leaves())


###### who and what question generation

def QG(sNLP, text):
    beVerbs = ["be", "am", "is", "are", "was", "were"]
    # create a parse tree
    # parseTree = sNLP.parse(text)
    # print(parseTree)

    # create a DEPENDENCY PARSE tree to understand the relation from the main verb
    dep_parse_Tree = sNLP.dependency_parse(text)
    dep_parse_Tree = dep_parse_Tree.__next__()
    Ques_list = []

    # be question

    # WHO question for Subject

    # create NER tags
    ner_tags = dict(sNLP.ner(text))
    # print(ner_tags)

    # get triples list of the dependency tree
    triples_list = list(dep_parse_Tree.triples())

    ##### LOOP THRU DEPENDENCY TREE AND CREATE QUESTIONS
    for this in triples_list:
        # print(this)
        if this[1] in ('nsubj','csubj'): # for the subject
            subject = this[2][0]
            if ner_tags[subject] == 'PERSON': # check if its a PERSON NER
                temp_text = text.replace(subject, "Who").replace(" .","?") # create question
                # some string manipulation to get the ?
                if "?" not in temp_text:
                    temp_text = temp_text + "?"

                Ques_list.append(temp_text) # add to list
                # print(text.replace(subject, "Who").replace(" .", "?"))

            if ner_tags[subject] == 'ORGANIZATION': # if the subject is ORG
                temp_text = text.replace(subject, "Which organization").replace(" .", "?")
                if "?" not in temp_text:
                    temp_text = temp_text + "?"

                Ques_list.append(temp_text)
                # print(text.replace(subject, "Who").replace(" .", "?"))
            if ner_tags[subject] == 'CITY': # if the subject is CITY
                temp_text = text.replace(subject, "Which city").replace(" .", "?")
                if "?" not in temp_text:
                    temp_text = temp_text + "?"

                Ques_list.append(temp_text)

            if ner_tags[subject] in ('O'): # if the subject is Other
                temp_text = contructQ(triples_list, subject, text, None)
                temp_text = temp_text.replace(subject, "What").replace(" .", "?")
                # for thisTuple in list(dep_parse_Tree.triples()):
                    # if this[0][0] == subject:
                if "?" not in temp_text:
                    temp_text = temp_text + "?"

                Ques_list.append(temp_text)
        if this[1] in ('iobj','dobj'):
            # code to be written for questions on direct and indirect Objects
            pass

    return (Ques_list)


#### in case of the subject has modifiers or the Subject is a part of a long NP remove all the related modifiers of the subject with the help of dependency tree
#### same to be replicated for Object as well
def contructQ(list_triples, subject, text, object):

    if subject is not None:
        text = text[text.find(subject):] ## removing unnecessary determinants (a, the, An) by slicing off until the subject word
        # print(text)
        dict_of_words_removed = {} # subject related word removal to construct a question
        for thisTriple in list_triples: ## loop thru dependency tree
            if thisTriple[0][0] == subject or thisTriple[0][0] in dict_of_words_removed:
                if (thisTriple[2][0]).lower() not in ('the','a','an'): # skipping determinants as they can be present in other places of the sentence as well
                    text = re.sub(' +',' ', text.replace(thisTriple[2][0],'')).strip() # removing subject related words
                    dict_of_words_removed[thisTriple[2][0]] = 0 # adding the removed word so that other words that are connected to this can also be removed
    # print(text)
    return(text)






if __name__ == '__main__':
    sNLP = StanfordNLP()

    ##### test sentences
    # text = 'Jefferson (1743–1826), the third U.S. President, was an amazing friend of George.'
    # text = 'Jefferson studied many subjects, like the artist Da Vinci'
    # text = 'However, Jefferson, who is a star student, studied many subjects in his childhood, like the artist Da Vinci.'
    # text = 'Jefferson studied many subjects, however failed in those subjects.'
    # text = "Being the third U.S. President, Jefferson knows his tricks well."
    text = "In 1946, when I talked with Julian, John was busy and the State of Venice liked my proposal."


    # print("Annotate:", sNLP.annotate(text))
    # print("POS:", sNLP.pos(text))
    # print("Tokens:", sNLP.word_tokenize(text))
    # print("NER:", sNLP.ner(text))



    # SENTENCE SIMPLIFICATION
    ### removing parenthetical phrases
    text = re.sub("\(.*\)", "", text)
    t = sNLP.parse(text)
    print("Parse:", t)

    # STEP 1: split on conjunctions
    t_list = []
    t_list = splitConjunctions(t, t_list, None)

    if len(t_list) == 0:
        t_list.append(t)
    print(t_list)


    # Simplify split parent sentences
    simplified_sentences = []
    for this in t_list:
        processed_text = " ".join(getNodes(this))
        processed_text = processed_text.replace(",","")
        processed_text = re.sub(' +', ' ', processed_text).strip()
        if processed_text[-1] != '.':
            processed_text += ' .'
        simplified_sentences.append(processed_text)
    print("Simplified Sentences...")
    print(simplified_sentences)

    #### Question generation
    final_q_list = []
    for this in simplified_sentences:
        final_q_list.extend(QG(sNLP, this))
    print("Questions...")
    print(final_q_list)

