import sys
import os
import operator
import numpy as np

#require nltk
import nltk
from nltk.tokenize import word_tokenize

class mymodel():
    def __init__(self):
        self.stat = {}

    def read(self, inFile):
        self.inFile  = open(inFile,"r").read()

    def token_parse(self):
        self.stat = {}
        #tokenize document to words
        Token = word_tokenize(self.inFile)
        sentence = []
        for i in range(len(Token)):
            sentence.append(Token[i])
            #select words to become sentences
            if Token[i] == '.':
                #use PoS tagger to parse sentences
                pos = nltk.pos_tag(sentence)
                #count the results of PoS tagger
                for pair in pos:
                    att = pair[1]
                    if att not in self.stat.keys():
                        self.stat[att]  = 1
                    else:
                        self.stat[att] += 1
                sentence = []

        print(self.stat)

if __name__ == '__main__':
    model = mymodel()
    #set dirName to the path of data
    dirName = "./data/set3/"
    for docName in os.listdir(dirName):
        if docName.split(".")[-1] != "txt":
            continue
        print(dirName+docName)
        model.read(dirName+docName)
        model.token_parse()




