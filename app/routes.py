from app import app, db
from app.models import Chat, Channel, Message, User, MessageExt
from app.helpers import getChannelChartLists, getUserChartLists, getWordLists, getChatAndChannelDict
from app.helpers import wordListMetrics, userMetrics, channelMetrics, chatMetrics
from app.helpers import getChatName, getChannelName, getUserName, getUserIds, getUserAttachmentList, getChannelIds
from app.helpers import chatChannelUserFilter
from datetime import timedelta
from flask import render_template, request, send_from_directory, abort, jsonify

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', **getChatAndChannelDict())

def getChannelAttachments(**kwargs):
    channelAttachments = {}
    userIds = getUserIds(**kwargs)
    for userName, userId in userIds.items():
        channelAttachments[userName] = getUserAttachmentList(userId=userId, **kwargs)
    return channelAttachments

def appendCloudToAttachments(channelAttachments, activeType, activeId):
    for userName, attachmentList in channelAttachments.items():
        path = '/'.join([activeType, str(activeId), userName])
        cloudURL = ''.join(['/dist/img/cloud/', path, '.png'])
        attachmentList.insert(0, cloudURL)
    return channelAttachments

def formatAsLabelDataArray(d, sort=False):
    if sort:
        return [{'label': k, 'data':v} for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)]
    else:
        return [{'label': k, 'data':v} for k, v in d.items()]

def getKeyList(key, **kwargs):
    if key == 'userId':
        return getUserIds(**kwargs)
    elif key == 'channelId':
        return getChannelIds(**kwargs)
    return {}

def _get_chart_data(metric, **kwargs):
    data = {}
    sort = False
    if metric.returnsDict():
        data = metric(**kwargs)
    else:
        key = metric.key() 
        if key in kwargs:
            print("ERROR, CANT HAVE KEY AS A SEARCH METRIC")
            return

        keyList = getKeyList(key, **kwargs)
        for keyName, keyId in keyList.items():
            data[keyName] = metric(**{key:keyId}, **kwargs)
        sort=True
    return jsonify(formatAsLabelDataArray(data, sort=sort))

ACTIVE_TYPES= {'channel': {'getName':getChannelName,'metricList':channelMetrics, 'idType':Channel.id },
               'chat': {   'getName':getChatName,   'metricList':chatMetrics,    'idType':Chat.id }}
def isValidURL(activeType, activeId):
    if activeType not in ACTIVE_TYPES.keys():
        return False
    if db.session.query(ACTIVE_TYPES[activeType]['idType']).filter_by(id=activeId).scalar() is None:  
        return False
    return True

def getActiveName(activeType, activeId):
    return ACTIVE_TYPES[activeType]['getName'](activeId)

def getActiveMetricList(activeType):
    return ACTIVE_TYPES[activeType]['metricList']

@app.route('/<string:activeType>/<int:activeId>')
def channel(activeType, activeId):
    if not isValidURL(activeType, activeId):
        abort(404)

    kwargs = {activeType+'Id':activeId}  
    attachments = appendCloudToAttachments(getChannelAttachments(**kwargs), activeType, activeId)
    return render_template('channel.html', **getChatAndChannelDict(), 
                                           charts=[x.name() for x in getActiveMetricList(activeType)],
                                           userCharts=[x.name() for x in userMetrics], 
                                           wordLists=[x.name() for x in wordListMetrics],
                                           usersIds=getUserIds(**kwargs),
                                           activeId=activeId,
                                           activeType=activeType,
                                           activeName=getActiveName(activeType, activeId),
                                           attachments=attachments)

@app.route('/<string:activeType>/<int:activeId>/_chart/<int:typeId>')
def _get_chatchannel_chart(activeType, activeId, typeId):
    if not isValidURL(activeType, activeId):
        abort(404)
    
    kwargs = {activeType+'Id':activeId}
    metricList = getActiveMetricList(activeType)
    if (typeId < len(metricList)):
        return _get_chart_data(metricList[typeId], **kwargs)
    abort(400)

@app.route('/<string:activeType>/<int:activeId>/_user_chart/<int:userId>/<int:typeId>')
def _get_user_chart(activeType, activeId, userId, typeId):
    if not isValidURL(activeType, activeId):
        abort(404)
    
    kwargs = {activeType+'Id':activeId, 'userId':userId}
    if (typeId < len(userMetrics)):
        return _get_chart_data(userMetrics[typeId], **kwargs)
    abort(400)

@app.route('/<string:activeType>/<int:activeId>/_user_words/<int:userId>/<int:typeId>')
def _get_user_words(activeType, activeId, userId, typeId):
    if not isValidURL(activeType, activeId):
        abort(404)

    kwargs = {activeType+'Id':activeId, 'userId':userId}
    if (typeId < len(wordListMetrics)):
        userCounts = wordListMetrics[typeId](**kwargs)
        return jsonify(formatAsLabelDataArray(userCounts, sort=True))
    abort(400)

def searchMessages(userName, word, **kwargs):
    messages = []
    for message in Message.query.filter(chatChannelUserFilter(**kwargs)).order_by(Message.timestamp).all():
        words = message.content.lower().split()
        if word in words:
            messages.append({'userName':userName, 
                             'content':message.content,
                             'id':message.id,
                             'timestamp':message.timestamp.strftime("%m/%d/%Y, %H:%M:%S")})
    return messages
#/messages/search/channel/1/1/lol
@app.route('/messages/search/<string:activeType>/<int:activeId>/<int:userId>/<string:word>')
def messageSearchPage(activeType, activeId, userId, word):
    if not isValidURL(activeType, activeId):
        abort(404)
    word = word.replace("HASHTAG", "#")
    userName = getUserName(userId)
    kwargs = {activeType+'Id':activeId, 'userId':userId}
    return render_template('messages.html', **getChatAndChannelDict(),
                                            headerString="Messages from {} containing '{}'".format(userName, word),
                                            messages=searchMessages(userName, word, **kwargs),
                                            activeId=activeId,
                                            activeName=getActiveName(activeType, activeId),
                                            activeType=activeType)

def searchMessagesTime(channelId, timestamp):
    messages = []
    timeFrom = timestamp - timedelta(hours=2)
    timeTo = timestamp + timedelta(hours=2)
    for message in Message.query.filter(Message.channel_id==channelId, Message.timestamp.between(timeFrom, timeTo)).order_by(Message.timestamp).all():
        messages.append({'userName':message.author.name, 
                            'content':message.content,
                            'id':message.id,
                            'timestamp':message.timestamp.strftime("%m/%d/%Y, %H:%M:%S")})
    return messages

@app.route('/messages/around/<int:messageId>')
def messagePage(messageId):
    if Message.query.filter_by(id=messageId).scalar() is None:
        abort(404)
    message = Message.query.get(messageId)
    timestamp = message.timestamp
    activeId = message.channel_id
    activeType = 'channel'
    return render_template('messages.html', **getChatAndChannelDict(),
                                            headerString="Messages",
                                            messages=searchMessagesTime(activeId, timestamp),
                                            activeId=activeId,
                                            activeName=getActiveName(activeType, activeId),
                                            activeType=activeType)

@app.route('/dist/<path:path>')
def send_dist(path):
    return send_from_directory('static/dist', path)

@app.route('/plugins/<path:path>')
def send_plugins(path):
    return send_from_directory('static/plugins', path)