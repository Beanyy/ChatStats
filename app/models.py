from app import db

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    channel = db.relationship('Channel', backref='chat', lazy='dynamic')
    def __repr__(self):
        return '<Chat {}>'.format(self.name)    

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    message = db.relationship('Message', backref='channel', lazy='dynamic')
    def __repr__(self):
        return '<Channel {}>'.format(self.name)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    message = db.relationship('Message', backref='author', lazy='dynamic')
    def __repr__(self):
        return '<User {}>'.format(self.name)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True)
    polarity = db.Column(db.Float)
    subjectivity = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'))
    messageExt = db.relationship('MessageExt', backref='message', lazy='dynamic')
    def __repr__(self):
        return '<Message {}>'.format(self.content)

class MessageExt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    extType = db.Column(db.Integer, index=True)
    count = db.Column(db.Integer, index=True, default=0)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    def __repr__(self):
        return '<MessageExt {} {}>'.format(self.extType, self.content)
