from datetime import datetime
from main_app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    class_cycle = db.Column(db.Integer)
    is_student = db.Column(db.Boolean, default=False)
    is_staff_member = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_guest = db.Column(db.Boolean, default=True)
    def __init__(self, username, email, class_cycle, password=None, is_student=False, is_staff_member=False, is_admin=False, is_guest=True):
        self.username = username
        self.email = email
        self.class_cycle = class_cycle
        self.is_student = is_student
        self.is_staff_member = is_staff_member
        self.is_admin = is_admin
        self.is_guest = is_guest
        if password:
            self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'class_cycle': self.class_cycle,
            'is_student': self.is_student,
            'is_staff_member': self.is_staff_member,
            'is_admin': self.is_admin,
            'is_guest': self.is_guest
        }
    
class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    s3_key = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)  
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=True)
    reply_id = db.Column(db.Integer, db.ForeignKey('forum_reply.id'), nullable=True)

    def __init__(self, filename, s3_key, file_type, file_size, post_id=None, reply_id=None):
        self.filename = filename
        self.s3_key = s3_key
        self.file_type = file_type
        self.file_size = file_size
        self.post_id = post_id
        self.reply_id = reply_id
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            's3_key': self.s3_key,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'post_id': self.post_id,
            'reply_id': self.reply_id
        }

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('forum_posts', lazy=True))
    attachments = db.relationship('Attachment', backref='post', lazy=True)
    cluster_id = db.Column(db.Integer, db.ForeignKey('forum_cluster.id'), nullable=True)

    def __init__(self, title, content, author_id, cluster_id, created_at=None):
        self.title = title
        self.content = content
        self.author_id = author_id
        self.cluster_id = cluster_id
        if created_at:
            self.created_at = created_at

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'author_id': self.author_id,
            'cluster_id': self.cluster_id,
            'attachments': [attachment.to_dict() for attachment in self.attachments]
        }


class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('forum_replies', lazy=True))
    post = db.relationship('ForumPost', backref=db.backref('replies', lazy=True))
    attachments = db.relationship('Attachment', backref='reply', lazy=True)

    def __init__(self, content, author_id, post_id, created_at=None):
        self.content = content
        self.author_id = author_id
        self.post_id = post_id
        if created_at:
            self.created_at = created_at

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'author_id': self.author_id,
            'post_id': self.post_id,
            'attachments': [attachment.to_dict() for attachment in self.attachments]
        }

class ForumCluster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('ForumPost', backref='cluster', lazy=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('forum_clusters', lazy=True))

    def __init__(self, name, author_id, description=None):
        self.name = name
        self.description = description
        self.author_id = author_id

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'author_id': self.author_id
        }

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    images = db.relationship('EventImage', backref='event', lazy=True, cascade="all, delete-orphan")

    def __init__(self, title, description=None):
        self.title = title
        self.description = description

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'images': [image.to_dict() for image in self.images]
        }

class EventImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    s3_key = db.Column(db.String(255), nullable=False, unique=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

    def __init__(self, s3_key, file_name, file_size, event_id):
        self.s3_key = s3_key
        self.file_name = file_name
        self.file_size = file_size
        self.event_id = event_id

    def to_dict(self):
        return {
            'id': self.id,
            's3_key': self.s3_key,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'event_id': self.event_id
        }
    
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    asked_at = db.Column(db.DateTime, default=datetime.utcnow)
    asker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    asker = db.relationship('User', backref=db.backref('asked_questions', lazy=True))
    is_answered = db.Column(db.Boolean, default=False)

    def __init__(self, question, asker_id, asked_at=None, is_answered=False):
        self.question = question
        self.asker_id = asker_id
        if asked_at:
            self.asked_at = asked_at
        self.is_answered = is_answered

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'asked_at': self.asked_at.isoformat() if self.asked_at else None,
            'asker_id': self.asker_id,
            'is_answered': self.is_answered
        }

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.Text, nullable=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    answerer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answerer = db.relationship('User', backref=db.backref('given_answers', lazy=True))
    question = db.relationship('Question', backref=db.backref('answers', lazy=True))

    def __init__(self, answer, answerer_id, question_id, answered_at=None):
        self.answer = answer
        self.answerer_id = answerer_id
        self.question_id = question_id
        if answered_at:
            self.answered_at = answered_at

    def to_dict(self):
        return {
            'id': self.id,
            'answer': self.answer,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None,
            'answerer_id': self.answerer_id,
            'question_id': self.question_id
        }

class CategoryLessons(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    lessons = db.relationship('Lesson', back_populates='category')

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'lessons': [lesson.to_dict() for lesson in self.lessons]
        }


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_audio = db.Column(db.Boolean, nullable=False) 
    s3_key = db.Column(db.String(255), nullable=False, unique=True)
    file_size = db.Column(db.Integer) 
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category_lessons.id'), nullable=False)
    category = db.relationship('CategoryLessons', back_populates='lessons')

    def __init__(self, title, description, is_audio, s3_key, file_size, category_id):
        self.title = title
        self.description = description
        self.is_audio = is_audio
        self.s3_key = s3_key
        self.file_size = file_size
        self.category_id = category_id

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'is_audio': self.is_audio,
            's3_key': self.s3_key,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'category_id': self.category_id
        }
