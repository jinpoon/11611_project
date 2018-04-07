import re
import os
import requests
from nltk.parse import stanford
from nltk.tokenize import word_tokenize
from collections import defaultdict
from stanfordcorenlp import StanfordCoreNLP
import json
from nltk.tree import *
import string
import nltk
import sys
from testscript import *

# os.environ['CLASSPATH'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27'
# os.environ[
#     'STANFORD_PARSER'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser.jar'
# os.environ[
#     'STANFORD_MODELS'] = '/Users/jovi/Desktop/CMU/NLP/project/stanford-parser-full-2015-12-09/stanford-parser-3.6.0-models.jar'

os.environ['CLASSPATH'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/jars'
os.environ['STANFORD_MODELS'] = '/Users/annamalaisenthilnathan/Desktop/NLP/11611_project-master/models'


class StanfordNLP:
    def __init__(self, host='http://localhost', port=9000):
        self.nlp = StanfordCoreNLP(host, port=port,
                                   timeout=30000)  # , quiet=False, logging_level=logging.DEBUG)

        # self.nlp = StanfordCoreNLP(r'/Users/jovi/Desktop/CMU/NLP/project/stanford-corenlp-full-2018-02-27')
        self.nlp_depParser = stanford.StanfordDependencyParser()
        self.nlp_parser = stanford.StanfordParser()

        self.props = {
            'annotators': 'coref',
            'pipelineLanguage': 'en'  # ,
            # 'outputFormat': 'json'
        }
        self.url = "http://localhost:9000"

    def word_tokenize(self, sentence):
        return self.nlp.word_tokenize(sentence)

    def pos(self, sentence):
        return self.nlp.pos_tag(sentence)

    def ner(self, sentence):
        return self.nlp.ner(sentence)

    def coref(self, text):
        if sys.version_info.major >= 3:
            text = text.encode('utf-8')
        props = {'annotators': 'coref', 'pipelineLanguage': 'en'}
        r = requests.post(self.url, params={'properties': str(props)}, data=text,
                          headers={'Connection': 'close'})
        return r.text

    def parse(self, sentence):
        return ParentedTree.convert(Tree.fromstring(self.nlp.parse(sentence)))

    # def dependency_parse(self, sentence):
    #     return self.nlp.dependency_parse(sentence)

    def dependency_parse(self, sentence):
        return self.nlp_depParser.raw_parse(sentence)

    def parser_sents(self, passage):
        return self.nlp_parser.raw_parse_sents(passage, )

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


class Simplification:
    ##### Split on conjunctions and some more simplifications in the complex parent sentence

    def __init__(self):
        self.sNLP = StanfordNLP()

    def coref_resolve(self, passage):
        text = "John is a tennis player. He has an awesome physique."
        result = json.loads(self.sNLP.coref(text))
        # print()
        # print(result['sentences'])
        print(len(list(result['corefs'].items())))
        num, mentions = list(result['corefs'].items())[0]
        for mention in mentions:
            print(mention)

    def splitConjunctions(self, parent, list_sents, firstPP):
        for node in parent:
            if type(node) is ParentedTree:
                if node.label() == 'ROOT':
                    print("======== Sentence =========")
                    print("Sentence:", " ".join(node.leaves()))
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
                    if firstPP is not None:
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
            print(sentence)
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
        print(ner_tags)

        # get triples list of the dependency tree
        triples_list = list(dep_parse_Tree.triples())
        print(triples_list)
        ##### LOOP THRU DEPENDENCY TREE AND CREATE QUESTIONS
        auxWord = 'xxx'
        for this in triples_list:
            # print(this)
            print('~~')
            print(this)
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


                print("sub", subject)
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
        print(text)
        return (text)
    # def QG(self, sentence):
    #     if len(sentence) < 3:
    #         return
    #     tree = parser.raw_parse_sents((sentence,))
    #     for i in tree:
    #         res = traversalAndSimplification(i)
    # print(res)
    # print(len(list(i)))
    # for j in res:
    # print(j)
    # print('------------------')

    # def token_parse(self):
    #     # print("________________________________________________")
    #     self.stat = 0
    #     Token = word_tokenize(self.textData)
    #     # Token = word_tokenize("English is a West Germanic language that was first spoken in early medieval England and is now a global lingua franca. It is an official language of almost 60 sovereign states, the most commonly spoken language in the United Kingdom, the United States, Canada, Australia, Ireland, and New Zealand, and a widely spoken language in countries in the Caribbean, Africa, and South Asia. It is the third most common native language in the world, after Mandarin and Spanish. It is the most widely learned second language and is an official language of the United Nations, of the European Union, and of many other world and regional international organisations. English has developed over the course of more than 1,400 years. The earliest forms of English, a set of Anglo-Frisian dialects brought to Great Britain by Anglo-Saxon settlers in the fifth century, are called Old English. Middle English began in the late 11th century with the Norman conquest of England. Early Modern English began in the late 15th century with the introduction of the printing press to London and the King James Bible as well as the Great Vowel Shift. Through the worldwide influence of the British Empire, modern English spread around the world from the 17th to mid-20th centuries. Through all types of printed and electronic media, as well as the emergence of the United States as a global superpower, English has become the leading language of international discourse and the lingua franca in many regions and in professional contexts such as science, navigation, and law.Modern English has little inflection compared with many other languages, and relies on auxiliary verbs and word order for the expression of complex tenses, aspect and mood, as well as passive constructions, interrogatives and some negation. Despite noticeable variation among the accents and dialects of English used in different countries and regions – in terms of phonetics and phonology, and sometimes also vocabulary, grammar and spelling – English speakers from around the world are able to communicate with one another effectively.English is an Indo-European language, and belongs to the West Germanic group of the Germanic languages. Most closely related to English are the Frisian languages, and English and Frisian form the Anglo-Frisian subgroup within West Germanic. Old Saxon and its descendent Low German languages are also closely related, and sometimes Low German, English, and Frisian are grouped together as the Ingvaeonic or North Sea Germanic languages. Modern English descends from Middle English, which in turn descends from Old English. Particular dialects of Old and Middle English also developed into a number of other English (Anglic) languages, including Scots and the extinct Fingallian and Forth and Bargy (Yola) dialects of Ireland.English is classified as a Germanic language because it shares new language features (different from other Indo-European languages) with other Germanic languages such as Dutch, German, and Swedish. These shared innovations show that the languages have descended from a single common ancestor, which linguists call Proto-Germanic. Some shared features of Germanic languages are the use of modal verbs, the division of verbs into strong and weak classes, and the sound changes affecting Proto-Indo-European consonants, known as Grimm's and Verner's laws. Through Grimm's law, the word for foot begins with /f/ in Germanic languages, but its cognates in other Indo-European languages begin with /p/. English is classified as an Anglo-Frisian language because Frisian and English share other features, such as the palatalisation of consonants that were velar consonants in Proto-Germanic.English sing, sang, sung; Dutch zingen, zong, gezongen; German singen, sang, gesungen (strong verb)English laugh, laughed; Dutch and German lachen, lachte (weak verb)English foot, German Fuß, Norwegian and Swedish fot (initial /f/ derived from Proto-Indo-European *p through Grimm's law)Latin pes, stem ped-; Modern Greek πόδι pódi; Russian под pod; Sanskrit पद् pád (original Proto-Indo-European *p)English cheese, Frisian tsiis (ch and ts from palatalisation)German Käse and Dutch kaas (k without palatalisation) English, like the other insular Germanic languages, Icelandic and Faroese, developed independently of the continental Germanic languages and their influences. English is thus not mutually intelligible with any continental Germanic language, differing in vocabulary, syntax, and phonology, although some, such as Dutch, do show strong affinities with English, especially with its earlier stages.Because English through its history has changed considerably in response to contact with other languages, particularly Old Norse and Norman French, some scholars have argued that English can be considered a mixed language or a creole – a theory called the Middle English creole hypothesis. Although the high degree of influence from these languages on the vocabulary and grammar of Modern English is widely acknowledged, most specialists in language contact do not consider English to be a true mixed language.")
    #     # Token = word_tokenize("I want a ski.")
    #     # print(Token)
    #     sentence = []
    #     self.texts = []
    #     beFlag = 0
    #     for i in range(len(Token)):
    #         sentence.append(Token[i])
    #         # if Token[i] in self.beWord:
    #         #     beFlag = 1
    #         # if Token[i] == '?':
    #         #     sentence = []
    #         #     beFlag = 0
    #         if Token[i] in {'.', ';', '!'}:
    #             # if beFlag:
    #             #     self.beWork(sentence)
    #             self.texts.append(' '.join(sentence))
    #             sentence = []
    #             beFlag = 0
    #     # print(self.texts)


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
    # def beWork(self, sentence):
    #     # pos = nltk.pos_tag(sentence)
    #     for i in range(len(sentence) - 1):
    #         if sentence[i] in self.beWord:
    #             j = i
    #             break
    #     temp = sentence[j]
    #     sentence.pop(j)
    #     sentence.insert(0, temp)
    #     # print(sentence)

    def preProcessText(self, text):
        data = re.sub("\(.*\)", "", text)
        data = re.sub(' +', ' ', data).strip()
        return data

    # def getSentenceList(self, text):
    #     result = json.loads(self.sNLP.coref(text))
    #     print("In sentence list")
    #     passage = []
    #
    #     for i in range(len(result['sentences'])):
    #         sentence = []
    #         tokens = result['sentences'][i]['tokens']
    #         print("tokens", tokens)
    #         for j in range(len(tokens)):
    #             word = tokens[j]['word'] #.lower()
    #             print("word", tokens[j]['word'])
    #             sentence.append(word)
    #         print(sentence)
    #         passage.append(sentence)
    #
    #     # for j in range(len())
    #     corefList = list(result['corefs'].items())
    #     print(corefList)
    #     # for each coreference group
    #     coreDic = {}
    #     for j in range(len(corefList)):
    #         corefItem = corefList[j][1]
    #         # print(corefItem)
    #         firstMention = []
    #         for k in range(len(corefList[j][1])):
    #             corefMention = corefItem[k]
    #             if corefMention['type'] != 'PRONOMINAL':
    #                 firstMention.append(k)
    #                 coreSymbol = '@COREF' + chr(j)
    #                 coreDic[coreSymbol] = corefMention['text']
    #                 break
    #
    #         for k in range(len(corefList[j][1])):
    #             corefMention = corefItem[k]
    #             if k not in firstMention:
    #                 sentNum = corefMention['sentNum']
    #                 coreSymbol = '@COREF' + chr(j)
    #                 for l in range(corefMention['startIndex'], corefMention['endIndex']):
    #                     # print(sentNum-1,l-1)
    #                     # print(len(passage))
    #                     passage[sentNum - 1][l - 1] = '@COREF*'
    #                     print(passage[sentNum - 1][l - 1])
    #                 passage[sentNum - 1][corefMention['startIndex'] - 1] = coreSymbol
    #                 print(coreSymbol)
    #     print(coreDic)
    #     for i in range(len(passage)):
    #         sentence = passage[i]
    #         for j in range(len(sentence)):
    #             if sentence[j] in coreDic.keys():
    #                 sentence[j] = coreDic[sentence[j]]
    #
    #     # finalPassage = []
    #
    #     for i in range(len(passage)):
    #         sent = []
    #         sentence = passage[i]
    #         for word in sentence:
    #             print(word)
    #             if word != "@COREF*":
    #                 sent.append(word)
    #         sentence = ' '.join(sent)
    #         print(sentence)
    #         self.sentence_list.append(sentence)
    #     print(self.sentence_list)

    def tokenizePara(self, textCorpus):
        Tokens = word_tokenize(textCorpus)
        sentence = []
        for i in range(len(Tokens)):
            sentence.append(Tokens[i])
            if Tokens[i] in {'.', ';', '!'}:
                self.sentence_list.append(' '.join(sentence))
                sentence = []
        pass
if __name__ == '__main__':
    ##### test sentences
    text = 'Jefferson (1743–1826), the third U.S. President, was an amazing friend of George.'
    # text = 'Jefferson studied many subjects, like the artist Da Vinci.'
    # text = 'However, Jefferson, who is a star student, studied many subjects in his childhood, like the artist Da Vinci.'
    # text = 'Jefferson studied many subjects, however failed in those subjects.'
    # text = "Being the third U.S. President, Jefferson knows his tricks well."
    ### have to test this some more
    # text = "In 1946, when I talked with Julian, John was busy and the State of Venice liked my proposal."
    # text = "I came from Pittsburgh."
    # text = "you arrive at Pittsburgh in 2018."
    # text = "I left the building from campus yesterday."
    # text = 'Jefferson (1743–1826), the third U.S. President, was an amazing friend of George. Jeff liked football.'
    # text = 'Dempsey became the first American player to score a hat-trick in the English Premier League , in the 5–2 win over Newcastle United in January 2012 .'
    # text = "John Black is a tennis player. He has an awesome physique. Jenny is a runner, and she is fit."
    # text = "NASA is a good company. It has many departments. Anna is an employee of it and she is well paid."
    # mainWork(text)

    ### Actual sentences
    # text = "The Old Kingdom is most commonly regarded as the period from the Third Dynasty through to the Sixth Dynasty."
    # text = "The Old Kingdom is the period in the third millennium (c. 2686-2181 BC) also known as the 'Age of the Pyramids' or 'Age of the Pyramid Builders' as it includes the great 4th Dynasty when King Sneferu perfected the art of pyramid building and the pyramids of Giza were constructed under the kings Khufu, Khafre, and Menkaure."
    # text = "The first Pharaoh of the Old Kingdom was Djoser of the third dynasty, who ordered the construction of a pyramid in Memphis' necropolis, Saqqara."
    # text = "After Djoser, Pharaoh Snefru was the next great pyramid builder."
    # text = "Snefru commissioned the building of not one, but three pyramids."
    # text = "The Meidum pyramid was the first to have an above-ground burial chamber."
    # text = "After Khufu's death, his sons Djedefra and Khafra may have quarrelled."
    # text = "Egypt was able to obtain wealth and stability under Ramesses' rule of over half a century."
    # text = "Egypt attained its first continuous peak of civilization â€“ the first of three so-called Kingdom periods (followed by the Middle Kingdom and New Kingdom) which mark the high points of civilization in the lower Nile Valley."
    # text = "The country slipped into civil wars mere decades after the close of Pepi II's reign."
    ## need to work on this (Tregex can be a solution)
    # text = "During the sixth dynasty the power of pharaoh gradually weakened in favor of powerful nomarchs (regional governors)."
    # text = "The first Pharaoh of the Old Kingdom was Djoser of the third dynasty, who ordered the construction of a pyramid in Memphis' necropolis, Saqqara. An important person during the reign of Djoser was his vizier, Imhotep."

    # Actual Paragraph
    # text = "The Old Kingdom is the period in the third millennium also known as the 'Age of the Pyramids' or 'Age of the Pyramid Builders' as it includes the great 4th Dynasty when King Sneferu perfected the art of pyramid building and the pyramids of Giza were constructed under the kings Khufu, Khafre, and Menkaure. Egypt attained its first continuous peak of civilization the first of three so-called Kingdom periods which mark the high points of civilization in the lower Nile Valley. The term itself was coined by eighteenth-century historians and the distinction between the Old Kingdom and the Early Dynastic Period is not one which would have been recognized by Ancient Egyptians. Not only was the last king of the Early Dynastic Period related to the first two kings of the Old Kingdom, but the 'capital', the royal residence, remained at Ineb-Hedg, the Ancient Egyptian name for Memphis. The basic justification for a separation between the two periods is the revolutionary change in architecture accompanied by the effects on Egyptian society and economy of large-scale building projects. " + \
    #         "The Old Kingdom is most commonly regarded as the period from the Third Dynasty through to the Sixth Dynasty. The 4th-6th Dynasties of Egypt, are scarce and historians regard the history of the era as literally 'written in stone' and largely architectural in that it is through the monuments and their inscriptions that scholars have been able to construct a history. "+\
    #         "Egyptologists also include the Memphite Seventh and Eighth Dynasties in the Old Kingdom as a continuation of the administration centralized at Memphis. While the Old Kingdom was a period of internal security and prosperity, it was followed by a period of disunity and relative cultural decline referred to by Egyptologists as the First Intermediate Period. During the Old Kingdom, the king of Egypt became a living god who ruled absolutely and could demand the services and wealth of his subjects. " + \
    #         "Under King Djoser, the first king of the Third Dynasty of the Old Kingdom, the royal capital of Egypt was moved to Memphis, where Djoser established his court. A new era of building was initiated at Saqqara under his reign. King Djoser's architect, Imhotep is credited with the development of building with stone and with the conception of the new architectural formâ€”the Step Pyramid. The Old Kingdom is perhaps best known for the large number of pyramids constructed at this time as burial places for Egypt's kings. For this reason, the Old Kingdom is frequently referred to as the Age of the Pyramids. "

    # text = "The first Pharaoh of the Old Kingdom was Djoser (sometime between 2691 and 2625 BC) of the third dynasty, who ordered the construction of a pyramid (the Step Pyramid) in Memphis' necropolis, Saqqara. An important person during the reign of Djoser was his vizier, Imhotep. "+\
    #        "It was in this era that formerly independent ancient Egyptian states became known as nomes, under the rule of the Pharaoh. The former rulers were forced to assume the role of governors or otherwise work in tax collection. Egyptians in this era worshipped their Pharaoh as a god, believing that he ensured the annual flooding of the Nile that was necessary for their crops. "+\
    #        "Egyptian views on the nature of time during this period held that the universe worked in cycles, and the Pharaoh on earth worked to ensure the stability of those cycles. They also perceived themselves as a specially selected people."

    # text = "The Old Kingdom and its royal power reached a zenith under the Fourth Dynasty, which began with Sneferu. After Djoser, Pharaoh Snefru was the next great pyramid builder. Snefru commissioned the building of not one, but three pyramids. The first is called the Meidum pyramid, named for its location in Egypt. "+\
    #        "Snefru abandoned it after the outside casing fell off of the pyramid. The Meidum pyramid was the first to have an above-ground burial chamber. Using more stones than any other Pharaoh, he built the three pyramids: a now collapsed pyramid in Meidum, the Bent Pyramid at Dahshur, and the Red Pyramid, at North Dahshur. "+\
    #        "However, the full development of the pyramid style of building was reached not at Saqqara, but during the building of 'The Great Pyramids' at Giza."

    # text = "Sneferu was succeeded by his son, Khufu, who built the Great Pyramid of Giza. After Khufu's death, his sons Djedefra and Khafra may have quarrelled. The latter built the second pyramid and the Sphinx in Giza. Recent reexamination of evidence has led Egyptologist Vassil Dobrev to propose that the Sphinx had been built by Djedefra as a monument to his father Khufu. Alternatively, the Sphinx has been proposed to be the work of Khafra and Khufu himself. "+\
    #        "There were military expeditions into Canaan and Nubia, with Egyptian influence reaching up the Nile into what is today the Sudan. The later kings of the Fourth Dynasty were king Menkaure, who built the smallest pyramid in Giza, Shepseskaf and, perhaps, Djedefptah."

    # text = "The Fifth Dynasty began with Userkaf and was marked by the growing importance of the cult of sun god Ra. Consequently, fewer efforts were devoted to the construction of pyramid complexes than during the 4th dynasty and more to the construction of sun temples in Abusir. Userkaf was succeeded by his son Sahure who commanded an expedition to Punt. Sahure was in turn succeeded by Neferirkare Kakai who was Sahure's son. Neferirkare introduced the prenomen in the royal titulary. He was followed by two short-lived kings, his son Neferefre and Shepseskare, the latter of uncertain parentage. Shepseskare may have been deposed by Neferefre's brother Nyuserre Ini, a long lived pharaoh who built extensively in Abusir and re-started royal activity in Giza. "+\
    #        "The last Pharaohs of the dynasty were Menkauhor Kaiu, Djedkare Isesi and Unas, the earliest ruler to have the pyramid texts inscribed in his pyramid."

    # text = "Egypt's expanding interests in trade goods such as ebony, incense such as myrrh and frankincense, gold, copper and other useful metals inspired the ancient Egyptians to build suitable ships for navigation of the open sea. They traded with Lebanon for cedar and travelled the length of the Red Sea to the Kingdom of Punt possibly modern day Somalia for ebony, ivory and aromatic resins. Ship builders of that era did not use pegs (treenails) or metal fasteners, but relied on rope to keep their ships assembled. Planks and the superstructure were tightly tied and bound together."

    # text = "During the sixth dynasty the power of pharaoh gradually weakened in favor of powerful nomarchs. These no longer belonged to the royal family and their charge became hereditary, thus creating local dynasties largely independent from the central authority of the Pharaoh. However, Nile flood control was still the subject of very large works, including especially the canal to Lake Moeris around 2300 BC, which was likely also the source of water to the Giza pyramid complex centuries earlier. "+\
    #        "Internal disorders set in during the incredibly long reign of Pepi II towards the end of the dynasty. His death, certainly well past that of his intended heirs, might have created succession struggles. The country slipped into civil wars mere decades after the close of Pepi II's reign."

    # text = "The final blow was the 22nd century BC drought in the region that resulted in a drastic drop in precipitation. For at least some years between 2200 and 2150 BC, this prevented the normal flooding of the Nile. "+\
    #        "Whatever its cause, the collapse of the Old Kingdom was followed by decades of famine and strife. An important inscription on the tomb of Ankhtifi, a nomarch during the early First Intermediate Period, describes the pitiful state of the country when famine stalked the land."

    # text = "Egypt's Old Kingdom was one of the most dynamic periods in the development of Egyptian art. During this period, artists learned to express their culture's worldview, creating for the first time images and forms that endured for generations. Architects and masons mastered the techniques necessary to build monumental structures in stone."

    # text = "Sculptors created the earliest portraits of individuals and the first lifesize statues in wood, copper, and stone. They perfected the art of carving intricate relief decoration and, through keen observation of the natural world, produced detailed images of animals, plants, and even landscapes, recording the essential elements of their world for eternity in scenes painted and carved on the walls of temples and tombs."

    # text = "These images and structures had two principal functions: to ensure an ordered existence and to defeat death by preserving life into the next world. To these ends, over a period of time, Egyptian artists adopted a limited repertoire of standard types and established a formal artistic canon that would define Egyptian art for more than 3,000 years, while remaining flexible enough to allow for subtle variation and innovation. Although much of their artistic effort was centered on preserving life after death, Egyptians also surrounded themselves with objects to enhance their lives in this world, producing elegant jewelry, finely carved and inlaid furniture, and cosmetic vessels and implements made from a wide range of materials."
    # pre-processing of text and getting list of sentences

    textManipulation = TextManipulator(text)
    list_sents = textManipulation.sentence_list
    for this in list_sents:
        print(this)
    ### NEED TO DO COREFERENCE HERE

    #creating the questions generation engine
    qgPipeline = QGPipeline()

    final_Ques = []
    for thisSent in list_sents:
        # get parse tree
        thisParseTree = qgPipeline.getParseTree(thisSent)
        # print(thisParseTree)
        thisParseTree.pretty_print()
        # separate conjun based questions
        no_conj_list = qgPipeline.splitConj(thisParseTree)
        # print(no_conj_list)
        # simplify sentences
        simpl_sents = qgPipeline.simplify_sentence(no_conj_list)
        # print(simpl_sents)
        # question collection
        final_Ques.extend(qgPipeline.QuesGen(simpl_sents))
        # print(final_Ques)

    for this in final_Ques:
        print(this)


    evaluator = QuestionEvaluator(productions_filename = "questionbank_pcfg.txt")

    # tups = []
    # with io.open(questions, 'r', encoding='utf8') as f:
        
    #   for line in f:
    #       line = line.strip()
    #       if(line[0:2] == '--'):
    #           symbol = '-'
    #           line = line[2:]
    #       else:
    #           symbol = '+'
    #       prob = evaluator.evaluate(line)
    #       tups.append((prob, line, symbol))
    # tups = sorted(tups)
    # print tups


    #evaluator.generate_pcfg_productions(questionbank)

    evaluations =[(evaluator.evaluate(i), i) for i in final_Ques]
    evaluations = sorted(evaluations)
    for i in evaluations:
        print(i)

    '''
    # model.token_parse()
    # for text in model.texts:
    #   mainWork(text)
    dirName = "../data/set1/"
    for i in range(1):#range(len(os.listdir(dirName))):
        docName = os.listdir(dirName)[i]
        if docName.split(".")[-1] != "txt":
            continue
        #print(dirName+docName)
        model.read(dirName+docName)
        model.token_parse()
        #for text in model.texts:
        #   mainWork(text)
    '''

    # url = "http://localhost:9000/tregex"
    # request_params = {"pattern": "(SBAR >> S)"}
    # # text = "Pusheen and Smitha walked along the beach."
    # r = requests.post(url, data=text, params=request_params)
    # temp = r.json()['sentences']
    # #print (temp[0]['parse'])
    # print(r.json())



'''
#TODO extractHelper
#TODO Decomposition of the Main Verb
#TODO passive voice
#TODO coreference
'''