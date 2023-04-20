from db import db

class Artist(db.Model):
        __tablename__ = 'artist'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        city = db.Column(db.String(120))
        state = db.Column(db.String(120))
        phone = db.Column(db.String(120))
        genres = db.Column(db.String(120))
        facebook_link = db.Column(db.String(120))
        image_link = db.Column(db.String(500))
        website_link = db.Column(db.String(120))
        seeking_venue = db.Column(db.Boolean, default=False)
        seeking_description = db.Column(db.String(500))

        shows = db.relationship('Show', backref='artist', lazy=True)

        def __repr__(self):
                return f'id={self.id}, name={self.name}'
