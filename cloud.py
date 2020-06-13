from app import db
from app.models import Chat, Channel, Message, User, MessageExt
from app.helpers import *
from datetime import date, timezone, timedelta
from dateutil import parser
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import os

def mkdirIfNotExists(dirName):
    if not os.path.exists(dirName):
        os.mkdir(dirName)

def isBlobEmoji(word):
    return re.match('^blob\w+', word) is not None

def filterWords(wordFreq):
    for word in myStopWords:
        if word in wordFreq:
            del wordFreq[word]
    return { k:v for k,v in wordFreq.items() if not (k.isnumeric() or isBlobEmoji(k))}

def adjustFreqs(wordFreqs, userWords):
    userTotalFreqs = {}
    for userName, userWordFreqs in userWords.items():
        userTotalFreqs[userName] = sum(userWordFreqs.values())

    totalFreqs = sum(wordFreqs.values())

    newWordFreqs = {}
    for word, count in wordFreqs.items():
        normalizedCounts = []
        for userName, userWordFreqs in userWords.items():
            if word in userWordFreqs:
                normalizedCounts.append(userWordFreqs[word]/userTotalFreqs[userName])
        avgNormalizedCounts = sum(normalizedCounts)/len(userWords)
        normalizedCount = count/totalFreqs
        newWordFreqs[word] = count*(normalizedCount/avgNormalizedCounts)
    return newWordFreqs

def generateClouds(fileName, wordFreq):
    wordcloud = WordCloud(width = 800, height = 800, 
            background_color ='black', 
            stopwords=None,
            min_font_size = 10).generate_from_frequencies(filterWords(wordFreq))
    fig = plt.figure(figsize = (8, 8), facecolor = None) 
    plt.imshow(wordcloud) 
    plt.axis("off") 
    plt.tight_layout(pad = 0) 
    if (fileName != None):
        print("Creating file", fileName)
        plt.savefig(fileName)
    else:
        plt.show()
    plt.close(fig)

def generateCloudFolder(folderName, userWords):
    for userName, wordFreq in userWords.items():
        if len(wordFreq) == 0:
            continue
        cloudFile = os.path.join(folderName, str(userName) + '.png')
        generateClouds(cloudFile, adjustFreqs(wordFreq, userWords))

def main():
    thisDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'app', 'static', 'dist','img', 'cloud')
    mkdirIfNotExists(thisDir)
    chatFolder = os.path.join(thisDir, 'chat')
    mkdirIfNotExists(chatFolder)
    channelFolder = os.path.join(thisDir, 'channel')
    mkdirIfNotExists(channelFolder)

    for chatId in getChatIds().values():
        chatDir = os.path.join(chatFolder, str(chatId))
        mkdirIfNotExists(chatDir)
        userWords = {}
        for userName, userId in getUserIds(chatId=chatId).items():
            userWords[userName] = filterWords(getWordList(userId=userId, chatId=chatId))
        generateCloudFolder(chatDir, userWords)

    for channelId in getChannelIds().values():
        channelDir = os.path.join(channelFolder, str(channelId))
        mkdirIfNotExists(channelDir)
        userWords = {}
        for userName, userId in getUserIds(channelId=channelId).items():
            userWords[userName] = filterWords(getWordList(userId=userId, channelId=channelId))
        generateCloudFolder(channelDir, userWords)

if __name__ == "__main__":
    main()
