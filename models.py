from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(100))
    admin_status = db.Column(db.Boolean, default=False)

class Filters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_filter = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(100), nullable=False)
    rel = db.relationship('VideoGame', backref='filters', uselist=False)

    def __repr__(self):
        return f'Category: {self.name_filter}'
    
class VideoGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    about_game = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('filters.id'))

    def __repr__(self):
        return f'GameName: {self.name}'
    
    def category_name(self):
        return Filters.query.filter_by(id=self.category_id).first().name_filter