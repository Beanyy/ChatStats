from app import app, db
from app.models import Chat, Channel, Message, User, MessageExt
from functools import lru_cache
from sqlalchemy.sql import and_
from textblob import TextBlob
from wordcloud import STOPWORDS
import re

def chatChannelUserFilter(userId=None, channelId=None, chatId=None):
    criterion = Message.channel_id.in_(resolveChannel(channelId=channelId, chatId=chatId))
    if userId is not None:
        criterion = and_(criterion, Message.user_id == userId)
    return criterion

@lru_cache()
def dbGetMessageExts(extType, **kwargs):
    return MessageExt.query.filter_by(extType=extType).join(MessageExt.message, aliased=True).filter(chatChannelUserFilter(**kwargs)).all()

@lru_cache()
def dbGetMessageContents(**kwargs):
    return db.session.query(Message.content).filter(chatChannelUserFilter(**kwargs)).all()

@lru_cache()
def dbGetMessageTimes(**kwargs):
    return db.session.query(Message.timestamp).filter(chatChannelUserFilter(**kwargs)).all()

@lru_cache(maxsize=None)
def dbGetChannels(chatId = None):
    if chatId is None:
        return db.session.query(Channel).all()
    else:
        return db.session.query(Channel).filter_by(chat_id=chatId).all()

@lru_cache(maxsize=None)
def dbGetChats():
    return db.session.query(Chat).all()

@lru_cache(maxsize=None)
def getChatChannelNames():
    chats = {}
    for channel in dbGetChannels():
        chat = chats.setdefault(channel.chat.name, [])
        chat.append(channel.name)
    return chats

@lru_cache(maxsize=None)
def getChatChannelIds():
    chatIds = {}
    for channel in dbGetChannels():
        chatIds.setdefault(channel.chat.id, [])
        chatIds[channel.chat.id].append(channel.id)
    return chatIds

@lru_cache()
def resolveChannel(channelId=None, chatId=None):
    if channelId is not None:
        return [channelId]
    elif chatId is not None:
        return getChatChannelIds()[chatId]
    return []

@lru_cache(maxsize=None)
def getChannelIds(**kwargs):
    channelIds = {}
    for channel in dbGetChannels(**kwargs):
        channelIds[channel.name] = channel.id
    return channelIds

@lru_cache(maxsize=None)
def getChatIds():
    chatIds = {}
    for chat in dbGetChats():
        chatIds[chat.name] = chat.id
    return chatIds

@lru_cache()
def getUserIds(**kwargs):
    userIds = {}
    dbUserIds = db.session.query(Message.user_id).filter(Message.channel_id.in_(resolveChannel(**kwargs))).distinct()
    users = db.session.query(User).filter(User.id.in_(dbUserIds)).all()
    for user in users:
        userIds[user.name] = user.id
    return userIds

@lru_cache()
def getChannelName(channelId):
    return Channel.query.get(channelId).name

@lru_cache()
def getChatName(chatId):
    return Chat.query.get(chatId).name

@lru_cache()
def getUserName(userId):
    return User.query.get(userId).name

@lru_cache()
def getReactionList(**kwargs):
    reactionCounts = {}
    for reaction in dbGetMessageExts(0, **kwargs):
        emoji = reaction.content
        reactionCounts.setdefault(emoji, 0)
        reactionCounts[emoji] += reaction.count
    return reactionCounts

IMG_EXTENSION_LIST = ["jpg", "jpeg", "jfif", "pjpeg", "pjp", "bmp", "png", "gif"]
def getUserAttachmentList(**kwargs):
    attachmentList = []
    for attachment in dbGetMessageExts(1, **kwargs):
        if attachment.content.split(".")[-1] in IMG_EXTENSION_LIST:
            attachmentList.append(attachment.content)
    return attachmentList

@lru_cache()
def getWordCounts(**kwargs):
    words = 0
    for message in dbGetMessageContents(**kwargs):
        words += len(message.content.split()) 
    return words

#Intentionally removing # and @ for this list
removePunctiationRegex = r'[\.\^\$\*\+\?\(\)\[\{\\\'\|’`:{}<>!”“",/~_=;%&-]+'
myStopWords = [re.sub(removePunctiationRegex, '', word) for word in STOPWORDS]
@lru_cache()
def getWordList(**kwargs):
    wordCounts = {}
    for message in dbGetMessageContents(**kwargs):
        words = message.content.split()
        for word in words:
            word = word.lower() #Lower case word
            if (word.find('http') >= 0): #Skip links
                continue
            word = re.sub(removePunctiationRegex, '', word)
            if (len(word) == 0 or word in myStopWords or word.isnumeric()):
                continue
            wordCounts.setdefault(word, 0)
            wordCounts[word] += 1
    return wordCounts

@lru_cache()
def getHashtagList(**kwargs):
    wordCounts = {}
    for message in dbGetMessageContents(**kwargs):
        words = message.content.split()
        for word in words:
            if (re.match('^#+', word) is None):
                continue
            word = word.lower() #Lower case word
            wordCounts.setdefault(word, 0)
            wordCounts[word] += 1
    return wordCounts

@lru_cache()
def getLolList(**kwargs):
    wordCounts = {}
    for message in dbGetMessageContents(**kwargs):
        words = message.content.split()
        for word in words:
            if (re.match('^[lL]+[oO]+[lL]+', word) is None):
                continue
            wordCounts.setdefault(word, 0)
            wordCounts[word] += 1
    return wordCounts

@lru_cache()
def getCharacterCounts(**kwargs):
    characters = 0
    for message in dbGetMessageContents(**kwargs):
        characters += len(message.content) 
    return characters

@lru_cache()
def getPolarity(**kwargs):
    polarities = []
    for message in db.session.query(Message.polarity).filter(chatChannelUserFilter(**kwargs)).all():
        polarities.append(message.polarity)

    if len(polarities) > 0:
        return sum(polarities)/len(polarities)
    return 0

@lru_cache()
def getSubjectivity(**kwargs):
    subjectivities = []
    for message in db.session.query(Message.subjectivity).filter(chatChannelUserFilter(**kwargs)).all():
        subjectivities.append(message.subjectivity)

    if len(subjectivities) > 0:
        return sum(subjectivities)/len(subjectivities)
    return 0

@lru_cache()
def getReactionCounts(**kwargs):
    return len(dbGetMessageExts(0, **kwargs))

@lru_cache()
def getAttachmentCounts(**kwargs):
    return len(dbGetMessageExts(1, **kwargs))

@lru_cache()
def getMessageCounts(**kwargs):
    return len(dbGetMessageContents(**kwargs))

def getAvgWordLength(**kwargs):
    return getCharacterCounts(**kwargs)/getWordCounts(**kwargs)

def getAvgMessageLength(**kwargs):
    return getCharacterCounts(**kwargs)/getMessageCounts(**kwargs)

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
@lru_cache()
def getTimeMonths(**kwargs):
    monthInfo = [0]*12
    for message in dbGetMessageTimes(**kwargs):
        time = message.timestamp
        monthInfo[time.month - 1] += 1
    return dict(zip(MONTHS, monthInfo))

HOURS = [str(x).zfill(2) for x in range(24)]
@lru_cache()
def getTimeHours(**kwargs):
    hourInfo = [0]*24
    for message in dbGetMessageTimes(**kwargs):
        time = message.timestamp
        hourInfo[time.hour] += 1
    return dict(zip(HOURS, hourInfo))

DAYSOFWEEK = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
WEEKHOURS = [DAYSOFWEEK[int(x/24)] + str(x%24).zfill(2) for x in range(24*7)]
@lru_cache()
def getTimeWeekHours(**kwargs):
    hourInfo = [0]*24*7
    for message in dbGetMessageTimes(**kwargs):
        time = message.timestamp
        sundayAsZeroWeekday = (time.weekday() + 1)%7
        hourInfo[time.hour + sundayAsZeroWeekday*24] += 1
    return dict(zip(WEEKHOURS, hourInfo))

class ChatMetric:
    def __init__(self, name, func, returnType=dict, key='userId'):
        self._func = func
        self._name = name
        self._returnType = returnType
        self._key = key
        pass

    def __call__(self, **kwargs):
        return self._func(**kwargs)

    def returnsDict(self):
        return self._returnType == dict

    def key(self):
        return self._key

    def name(self):
        return self._name

channelMsgCnts = ChatMetric('ChannelMessages', getMessageCounts, returnType=int, key='channelId')
channelReactions = ChatMetric('ChannelReactions', getReactionCounts, returnType=int, key='channelId')
channelMsgCnts = ChatMetric('ChannelAttachment', getAttachmentCounts, returnType=int, key='channelId')

msgCnts = ChatMetric('MsgCounts', getMessageCounts, returnType=int)
wrdCnts = ChatMetric('WordCounts', getWordCounts, returnType=int)
charCnts = ChatMetric('AvgWordLength', getAvgWordLength, returnType=int)
msgSize = ChatMetric('AvgMsgLength', getAvgMessageLength, returnType=int)
polarityCnts = ChatMetric('Polarity', getPolarity, returnType=int)
subjectivityCnts = ChatMetric('Subjectivity', getSubjectivity, returnType=int)
reactionCnts = ChatMetric('Reactions', getReactionCounts, returnType=int)
attachmentCnts = ChatMetric('Attachments', getAttachmentCounts, returnType=int)

monAct = ChatMetric('MonthlyPosts', getTimeMonths)
hourAct = ChatMetric('HourlyPosts', getTimeHours)
weekAct = ChatMetric('HourlyWeekPosts', getTimeWeekHours)

wordList = ChatMetric('Word', getWordList)
reactionList = ChatMetric('Reaction', getReactionList)
hashtagList = ChatMetric('Hashtags', getHashtagList)
lolList = ChatMetric('lol', getLolList)

wordListMetrics = [wordList, reactionList, hashtagList, lolList]
userMetrics = [monAct, hourAct, weekAct]
channelMetrics = [msgCnts, wrdCnts, charCnts, msgSize, polarityCnts, subjectivityCnts, reactionCnts, attachmentCnts]  + userMetrics
chatMetrics = [channelMsgCnts, channelReactions, channelMsgCnts] + channelMetrics

def getChannelChartLists():
    return {'charts': [x.name() for x in channelMetrics]}

def getUserChartLists():
    return {'userCharts': [x.name() for x in userMetrics]}

def getWordLists():
    return {'wordLists': [x.name() for x in wordListMetrics]}

@lru_cache(maxsize=None)
def getChatAndChannelDict():
    return {'chats': getChatChannelNames(),
            'channelIds': getChannelIds(),
            'chatIds': getChatIds()}