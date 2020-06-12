from app import db
from app.models import Chat, Channel, Message, User, MessageExt
import json
import glob
from datetime import date, timezone, timedelta
from dateutil import parser
from textblob import TextBlob
import re

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        db.session.flush()
        return instance

def addMessage(channel, user, content, isoTime):
    date = parser.isoparse(isoTime).astimezone(timezone(-timedelta(hours=4)))
    if (date.year != 2019):
        return None
    sentiment = TextBlob(content).sentiment
    message = Message(content=content,
                        timestamp=date,
                        user_id=user.id,
                        channel_id=channel.id,
                        polarity=sentiment.polarity,
                        subjectivity=sentiment.subjectivity)
    db.session.add(message) 
    return message

def addMessageExt(message, content, extType, count=0):
    db.session.flush()
    msgExt = MessageExt(content=content, count=count, extType=extType, message_id=message.id)
    db.session.add(msgExt)
    return msgExt

def addMessagesFromChannel(channel, file):
    data = None
    with open(file) as json_file:
        data = json.load(json_file)

    for message in data['messages']:
        if (message['author']['isBot']):
            continue

        isoTime = message['timestamp']
        userName = message['author']['name']
        content = message['content']
        
        if re.match('^PokerStars ', content) is not None:
            print(content)
            continue

        user = get_or_create(db.session, User, name=userName)
        dbMessage = addMessage(channel, user, content, isoTime)
        if dbMessage is None:
            continue

        for reaction in message['reactions']:
            addMessageExt(dbMessage, reaction['emoji']['name'], 0, count=reaction['count'])
        for attachment in message['attachments']:
            addMessageExt(dbMessage, attachment['url'], 1)

def main():
    db.create_all()
    for file in glob.glob("chats/*.json"):
        chatName, tmp = file.split('-', 1)
        chatName = chatName[6:].replace(' ','')
        chat = get_or_create(db.session, Chat, name=chatName)
        
        channelName, _ = tmp.split('[', 1)
        channelName = channelName.replace(' ','')
        channel = get_or_create(db.session, Channel, name=channelName, chat_id=chat.id)
        print(channelName)
        addMessagesFromChannel(channel, file)
    db.session.commit()

if __name__ == "__main__":
    main()
