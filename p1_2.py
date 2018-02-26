import sys
import os
import operator
import numpy as np
import nltk
from nltk.tokenize import word_tokenize

class mymodel():
    def __init__(self):
        self.stat = {}

    def read(self, inFile):
        self.inFile  = open(inFile,"r").read()

    def token_parse(self):
        #print("________________________________________________")
        self.stat = 0
        Token = word_tokenize(self.inFile)
        #Token = word_tokenize("English is a West Germanic language that was first spoken in early medieval England and is now a global lingua franca. It is an official language of almost 60 sovereign states, the most commonly spoken language in the United Kingdom, the United States, Canada, Australia, Ireland, and New Zealand, and a widely spoken language in countries in the Caribbean, Africa, and South Asia. It is the third most common native language in the world, after Mandarin and Spanish. It is the most widely learned second language and is an official language of the United Nations, of the European Union, and of many other world and regional international organisations. English has developed over the course of more than 1,400 years. The earliest forms of English, a set of Anglo-Frisian dialects brought to Great Britain by Anglo-Saxon settlers in the fifth century, are called Old English. Middle English began in the late 11th century with the Norman conquest of England. Early Modern English began in the late 15th century with the introduction of the printing press to London and the King James Bible as well as the Great Vowel Shift. Through the worldwide influence of the British Empire, modern English spread around the world from the 17th to mid-20th centuries. Through all types of printed and electronic media, as well as the emergence of the United States as a global superpower, English has become the leading language of international discourse and the lingua franca in many regions and in professional contexts such as science, navigation, and law.Modern English has little inflection compared with many other languages, and relies on auxiliary verbs and word order for the expression of complex tenses, aspect and mood, as well as passive constructions, interrogatives and some negation. Despite noticeable variation among the accents and dialects of English used in different countries and regions – in terms of phonetics and phonology, and sometimes also vocabulary, grammar and spelling – English speakers from around the world are able to communicate with one another effectively.English is an Indo-European language, and belongs to the West Germanic group of the Germanic languages. Most closely related to English are the Frisian languages, and English and Frisian form the Anglo-Frisian subgroup within West Germanic. Old Saxon and its descendent Low German languages are also closely related, and sometimes Low German, English, and Frisian are grouped together as the Ingvaeonic or North Sea Germanic languages. Modern English descends from Middle English, which in turn descends from Old English. Particular dialects of Old and Middle English also developed into a number of other English (Anglic) languages, including Scots and the extinct Fingallian and Forth and Bargy (Yola) dialects of Ireland.English is classified as a Germanic language because it shares new language features (different from other Indo-European languages) with other Germanic languages such as Dutch, German, and Swedish. These shared innovations show that the languages have descended from a single common ancestor, which linguists call Proto-Germanic. Some shared features of Germanic languages are the use of modal verbs, the division of verbs into strong and weak classes, and the sound changes affecting Proto-Indo-European consonants, known as Grimm's and Verner's laws. Through Grimm's law, the word for foot begins with /f/ in Germanic languages, but its cognates in other Indo-European languages begin with /p/. English is classified as an Anglo-Frisian language because Frisian and English share other features, such as the palatalisation of consonants that were velar consonants in Proto-Germanic.English sing, sang, sung; Dutch zingen, zong, gezongen; German singen, sang, gesungen (strong verb)English laugh, laughed; Dutch and German lachen, lachte (weak verb)English foot, German Fuß, Norwegian and Swedish fot (initial /f/ derived from Proto-Indo-European *p through Grimm's law)Latin pes, stem ped-; Modern Greek πόδι pódi; Russian под pod; Sanskrit पद् pád (original Proto-Indo-European *p)English cheese, Frisian tsiis (ch and ts from palatalisation)German Käse and Dutch kaas (k without palatalisation) English, like the other insular Germanic languages, Icelandic and Faroese, developed independently of the continental Germanic languages and their influences. English is thus not mutually intelligible with any continental Germanic language, differing in vocabulary, syntax, and phonology, although some, such as Dutch, do show strong affinities with English, especially with its earlier stages.Because English through its history has changed considerably in response to contact with other languages, particularly Old Norse and Norman French, some scholars have argued that English can be considered a mixed language or a creole – a theory called the Middle English creole hypothesis. Although the high degree of influence from these languages on the vocabulary and grammar of Modern English is widely acknowledged, most specialists in language contact do not consider English to be a true mixed language.")
        #Token = word_tokenize("I want a ski.")
        #print(Token)
        sentence = []
        for i in range(len(Token)):
            sentence.append(Token[i])
            if Token[i] == '.':
                pos = nltk.pos_tag(sentence)
                #print(pos)
                for pair in pos:
                    att = pair[1]
                    if att[:2]=="NN":
                        self.stat += 1
                    #if att not in self.stat.keys():
                    #    self.stat[att]  = 1
                    #else:
                    #    self.stat[att] += 1
                #print('-------------------------------')
                sentence = []

        #print(self.inToken)
        print(self.stat)

if __name__ == '__main__':
    
    model = mymodel()
    dirName = "./data/set3/"
    for i in range(len(os.listdir(dirName))):
        docName = os.listdir(dirName)[i]
        if docName.split(".")[-1] != "txt":
            continue
        print(dirName+docName)
        model.read(dirName+docName)
        model.token_parse()

    #print (model.stat)


