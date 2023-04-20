from db import db

class Venue(db.Model):
        __tablename__ = 'venue'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        city = db.Column(db.String(120), nullable=False)
        state = db.Column(db.String(120), nullable=False)
        address = db.Column(db.String(120), nullable=False)
        phone = db.Column(db.String(120), nullable=False)
        genres = db.Column(db.String(120))
        facebook_link = db.Column(db.String(120))
        image_link = db.Column(db.String(500))
        website_link = db.Column(db.String(120))
        seeking_talent = db.Column(db.Boolean, default=False)
        seeking_description = db.Column(db.String(500))

        shows = db.relationship('Show', backref='venue', lazy=True)

        def __repr__(self):
                return f'id={self.id}, name={self.name}'
