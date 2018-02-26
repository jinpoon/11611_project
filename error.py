import sys
import os
import operator
import numpy as np
import nltk
from nltk.tokenize import word_tokenize

class mymodel():
    def __init__(self):
        self.stat = {}
        self.gt1  = 0
        self.pr1  = 0
        self.ov1  = 0
        self.nn = ["NNS","NNP","NN"]

    def read(self, inFile):
        self.inFile  = open(inFile,"r").read()
        self.gt      = open("gt.txt","r").read().split("\n")
        print(self.gt)

    def tsmall(self, word):
        result = []
        #print(word )
        for i in range(len(word)):
            c = word[i]
            if ord(c)>=ord('A') and ord(c)<=ord('Z'):
                c = chr(ord('a')+ord(c)-ord('A'))
            result.append(c)
        ##print(''.join(result))
        return ''.join(result)

    def token_parse(self):
        self.stat = {}
        Token = word_tokenize(self.inFile)
        Token = word_tokenize("English is a West Germanic language that was first spoken in early medieval England and is now a global lingua franca. It is an official language of almost 60 sovereign states, the most commonly spoken language in the United Kingdom, the United States, Canada, Australia, Ireland, and New Zealand, and a widely spoken language in countries in the Caribbean, Africa, and South Asia. It is the third most common native language in the world, after Mandarin and Spanish. It is the most widely learned second language and is an official language of the United Nations, of the European Union, and of many other world and regional international organisations. English has developed over the course of more than 1,400 years. The earliest forms of English, a set of Anglo-Frisian dialects brought to Great Britain by Anglo-Saxon settlers in the fifth century, are called Old English. Middle English began in the late 11th century with the Norman conquest of England. Early Modern English began in the late 15th century with the introduction of the printing press to London and the King James Bible as well as the Great Vowel Shift. Through the worldwide influence of the British Empire, modern English spread around the world from the 17th to mid-20th centuries. Through all types of printed and electronic media, as well as the emergence of the United States as a global superpower, English has become the leading language of international discourse and the lingua franca in many regions and in professional contexts such as science, navigation, and law. Modern English has little inflection compared with many other languages, and relies on auxiliary verbs and word order for the expression of complex tenses, aspect and mood, as well as passive constructions, interrogatives and some negation. Despite noticeable variation among the accents and dialects of English used in different countries and regions – in terms of phonetics and phonology, and sometimes also vocabulary, grammar and spelling – English speakers from around the world are able to communicate with one another effectively.")
        
        #print(Token)
        sentence = []
        j = 0
        for i in range(len(Token)):
            sentence.append(Token[i])
            if Token[i] == '.':
                pos = nltk.pos_tag(sentence)
                print(pos)
                for k in range(len(sentence)):
                    word = self.gt[j].split(' ')[0]
                    word = self.tsmall(word)
                    label = self.gt[j].split(' ')[1]
                    pdword = pos[k][0]
                    pdword = self.tsmall(pdword)
                    pdlabel = pos[k][1]
                    #print(word, pdword)
                    if pdword == word:
                        if pdlabel[:2]=="NN":
                            self.pr1 += 1
                        if label == "1":
                            self.gt1 += 1
                        if pdlabel[:2]=="NN" and label == "1":
                            self.ov1 += 1
                        if (pdlabel[:2]=="NN") ^ (label == "1"):
                            print("!!!",word, pdword)
                            print("!!!",label,pdlabel)
                        j+=1

                for pair in pos:
                    att = pair[1]
                    if att not in self.stat.keys():
                        self.stat[att]  = 1
                    else:
                        self.stat[att] += 1
                #print('-------------------------------')
                sentence = []

        #print(self.inToken)
        print(self.stat)
        print(self.pr1)
        print(self.gt1)
        print(self.ov1)


if __name__ == '__main__':
    
    model = mymodel()
    dirName = "./data/set3/"
    model.read("./data/set3/a1.txt")
    model.token_parse()
    #print (model.stat)


