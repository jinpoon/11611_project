import re
import os
import requests
from nltk.parse import stanford
from collections import defaultdict
from stanfordcorenlp import StanfordCoreNLP
import json
from nltk.tree import *
import string

os.environ['CLASSPATH'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27'
os.environ['STANFORD_PARSER'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'

class StanfordNLP:
    def __init__(self, host='http://localhost', port=9000):
        self.nlp = StanfordCoreNLP(host, port=port,
                                   timeout=30000)  # , quiet=False, logging_level=logging.DEBUG)

        #self.nlp = StanfordCoreNLP(r'/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27')
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


def auxilaryWord(sub):
	# TODO lowercase
	# TODO will may...
	# TODO plural...
	# Jerry and I
	if sub in ('I', 'they', 'you'):
		return 'do'
	if sub in ('he', 'she'):
		return 'dose'

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
    print('++++')
    print(text)
    ner_tags = dict(sNLP.ner(text))
    pos_tag  = sNLP.pos(text)
    print(ner_tags)

    # get triples list of the dependency tree
    triples_list = list(dep_parse_Tree.triples())
    print(triples_list)
    print('++++')

    ##### LOOP THRU DEPENDENCY TREE AND CREATE QUESTIONS
    auxWord = 'xxx'
    for this in triples_list:
        # print(this)
        print('~~')
        print(this)
        temp_text = '?'

        
        if this[1] in ('nummod'): # for number
            numPhrase = this[2][0] + ' ' + this[0][0] 
            targetWord = this[2][0]
            if ner_tags[targetWord] in ('NUMBERS'):
                temp_text = text.replace(numPhrase, "").replace(" .","?")
                temp_text = "How many " + this[0][0] + " " + auxWord + " " + temp_text 
 

        if this[1] in ('case'):       # for prop
            subject = this[0][0]
            propPhrase = this[2][0] + ' ' + this[0][0]
            print(propPhrase)
            if ner_tags[subject] in ('CITY'): # where
                temp_text = text.replace(propPhrase, "").replace(" .","?") # create question
                temp_text = "Where " + auxWord + " " + temp_text 
                # some string manipulation to get the ?
            if ner_tags[subject] in ('DATE'): # when
                temp_text = text.replace(propPhrase, "").replace(" .","?")
                temp_text = "When " + auxWord + " " + temp_text 
         

        if this[1] in ('nsubj','csubj'): # for the subject
            subject = this[2][0]
            auxWord = auxilaryWord(this[2][0])
            if ner_tags[subject] == 'PERSON': # check if its a PERSON NER
                temp_text = text.replace(subject, "Who").replace(" .","?") # create question
                # some string manipulation to get the ?
                if "?" not in temp_text:
                    temp_text = temp_text + "?"          
                # print(text.replace(subject, "Who").replace(" .", "?"))
            
            if ner_tags[subject] == 'ORGANIZATION': # if the subject is ORG
                temp_text = text.replace(subject, "Which organization").replace(" .", "?")
                # print(text.replace(subject, "Who").replace(" .", "?"))
            if ner_tags[subject] == 'CITY': # if the subject is CITY
                temp_text = text.replace(subject, "Which city").replace(" .", "?")
            if this[2][1] in 'PRP':
            	temp_text = text.replace(subject, "Who").replace(" .", "?")
            if ner_tags[subject] in ('O') and temp_text == '?': # if the subject is Other
                temp_text = contructQ(triples_list, subject, text, None)
                temp_text = temp_text.replace(subject, "What").replace(" .", "?")
                # for thisTuple in list(dep_parse_Tree.triples()):
                    # if this[0][0] == subject:
            

            
        if this[1] in ('iobj','dobj'):
            # code to be written for questions on direct and indirect Objects
            pass
        #### endif 
        if "?" not in temp_text:
            temp_text = temp_text + "?"
        if temp_text != '?':
            print(temp_text)
            Ques_list.append(temp_text)

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
    # text = "In 1946, when I talked with Julian, John was busy and the State of Venice liked my proposal."
    # text = "I came from Pittsburgh."
    # text = "you arrive at Pittsburgh in 2018."
    text = "I buy 5 apples at Pittsburgh in 2018."

    '''
    url = "http://localhost:9000/#div_tregex"
    request_params = {"pattern": "(NP[$VP]>S)|(NP[$VP]>S\\n)|(NP\\n[$VP]>S)|(NP\\n[$VP]>S\\n)"}
    text = "Pusheen and Smitha walked along the beach."
    r = requests.post(url, data=text, params=request_params)
    temp = r.json()['sentences']
    print (temp[0]['parse'])
    '''
    

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
'''
#TODO extractHelper
#TODO post-processing input: question output: (do does did will may)
#TODO passive voice

'''