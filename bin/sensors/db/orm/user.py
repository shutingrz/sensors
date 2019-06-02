from sensors import db


class User(db.Model):
    def __init__(self, user_id, email):
        self.user_id = user_id
        self.email = email


db.mapper(User, db.Table('user', db.metadata, autoload=True))
