import dateutil.parser
import babel
import logging
import sys

from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from logging import Formatter, FileHandler
from forms import *
from sqlalchemy import func

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
session = db.session

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

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


class Show(db.Model):
        __tablename__ = 'show'

        id = db.Column(db.Integer, primary_key=True)
        artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
        venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
        start_time = db.Column(db.DateTime, nullable=False)

        def __repr__(self):
                return f'id={self.id}, artist={self.artist_id}, venue={self.venue_id}'


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
            format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
            format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#    Venues
#    ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    locations_unique = session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state).all()
    for i in locations_unique:
        city = i[0]
        state = i[1]
        venues = []

        venues_data = session.query(Venue).filter(Venue.city==city, Venue.state==state).all()
        for j in venues_data:
            venue = {
                'id': j.id,
                'name': j.name,
                'num_upcoming_shows': 0,
            }
            venues.append(venue)

        data.append({
                'city': city,
                'state': state,
                'venues': venues,
        })

    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # case-insensitive search
    venues = session.query(Venue).filter(Venue.name.ilike('%{}%'.format(request.form['search_term']))).all()
    data = []
    for i in venues:
        num_upcoming_shows = session.query(Show.id).filter(
            Show.venue_id == i.id,
            Show.start_time > func.now(),
        ).count()

        data.append({
            'id': i.id,
            'name': i.name,
            'num_upcoming_shows': num_upcoming_shows,
        })

    response = {
        'count': len(venues),
        'data': data,
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue_data = Venue.query.get(venue_id)

    past_shows = []
    upcoming_shows = []
    shows = session.query(
        Artist.id,
        Artist.name,
        Artist.image_link,
        Show.start_time,
    ).join(Artist).filter(Show.venue_id==venue_id).all()

    for i in shows:
        show_info = {
            'artist_id': i[0],
            'artist_name': i[1],
            'artist_image_link': i[2],
            'start_time': str(i[3]),
        }

        if i[3] > datetime.now():
            upcoming_shows.append(show_info)
        else:
            past_shows.append(show_info)
    
    venue = {
        "id": venue_id,
        "name": venue_data.name,
        # e.g. '{Classical,Hip-Hop,R&B}' -> ['Classical', 'Hip-Hop', 'R&B']
        "genres": venue_data.genres.strip('{}').split(','),
        "address": venue_data.address,
        "city": venue_data.city,
        "state": venue_data.state,
        "phone": venue_data.phone,
        "website": venue_data.website_link,
        "facebook_link": venue_data.facebook_link,
        "seeking_talent": venue_data.seeking_talent,
        "seeking_description": venue_data.seeking_description,
        "image_link": venue_data.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=venue)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    if form.validate():
        try:
            new_venue = Venue(
                name = request.form['name'],
                city = request.form['city'],
                state = request.form['state'],
                address = request.form['address'],
                phone = request.form['phone'],
                image_link = request.form['image_link'],
                genres = request.form.getlist('genres', type=str),
                facebook_link = request.form['facebook_link'],
                website_link = request.form['website_link'],
                seeking_talent = "seeking_talent" in request.form,
                seeking_description = request.form['seeking_description']
            )

            session.add(new_venue)
            session.commit()
            # on successful db insert, flash success
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
            return redirect(url_for('show_venue', venue_id=Venue.query.order_by(Venue.id.desc()).first().id))
            
        except Exception as e:
            session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

        finally:
            session.close()

        return render_template('pages/home.html')

    else:
        for message in form.errors.items():
            # e.g. ('phone', ['Invalid phone number format.']) -> Invalid phone number format.
            flash(message[1][0], 'warning')
        
        return redirect(request.referrer)


@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        venue_name = venue.name
        session.delete(venue)
        session.commit()
        flash('Venue ' + venue_name + ' was successfully deleted!')

    except Exception as e:
        session.rollback()
        print(e, flush=True)
        flash('An error occurred. The venue (ID: ' + venue_id + ') could not be deleted.')
    
    finally:
        session.close()
    
    return jsonify({'success': True})


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id).__dict__

    form.name.data = venue['name']
    form.city.data = venue['city']
    form.state.data = venue['state']
    form.phone.data = venue['phone']
    form.image_link.data = venue['image_link']
    form.genres.data = venue['genres']
    form.address.data = venue['address']
    form.facebook_link.data = venue['facebook_link']
    form.website_link.data = venue['website_link']
    form.seeking_talent.data = venue['seeking_talent']
    form.seeking_description.data = venue['seeking_description']

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    if form.validate():
        try:
            venue = Venue.query.get(venue_id)

            venue.name = request.form['name']
            venue.city = request.form['city']
            venue.state = request.form['state']
            venue.address = request.form['address']
            venue.phone = request.form['phone']
            venue.image_link = request.form['image_link']
            venue.genres = request.form.getlist('genres', type=str)
            venue.facebook_link = request.form['facebook_link']
            venue.website_link = request.form['website_link']
            venue.seeking_talent = "seeking_talent" in request.form
            venue.seeking_description = request.form['seeking_description']

            session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully edited!')
            
        except Exception as e:
            session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')

        finally:
            session.close()

        return redirect(url_for('show_venue', venue_id=venue_id))

    else:
        for message in form.errors.items():
            # e.g. ('phone', ['Invalid phone number format.']) -> Invalid phone number format.
            flash(message[1][0], 'warning')

        return redirect(request.referrer)


#    Artists
#    ----------------------------------------------------------------

@app.route('/artists')
def artists():
    data = []
    artists = session.query(Artist.id, Artist.name).all()
    for i in artists:
        data.append({
                'id': i[0],
                'name': i[1],
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # case-insensitive search
    artists = session.query(Artist).filter(Artist.name.ilike('%{}%'.format(request.form['search_term']))).all()
    data = []
    for i in artists:
        num_upcoming_shows = session.query(Show.id).filter(
            Show.artist_id == i.id,
            Show.start_time > func.now(),
        ).count()

        data.append({
            'id': i.id,
            'name': i.name,
            'num_upcoming_shows': num_upcoming_shows,
        })

    response = {
        'count': len(artists),
        'data': data,
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist_data = Artist.query.get(artist_id)

    past_shows = []
    upcoming_shows = []
    shows = session.query(
        Venue.id,
        Venue.name,
        Venue.image_link,
        Show.start_time,
    ).join(Venue).filter(Show.artist_id==artist_id).all()

    for i in shows:
        show_info = {
            'venue_id': i[0],
            'venue_name': i[1],
            'venue_image_link': i[2],
            'start_time': str(i[3]),
        }

        if i[3] > datetime.now():
            upcoming_shows.append(show_info)
        else:
            past_shows.append(show_info)
    
    artist = {
        "id": artist_id,
        "name": artist_data.name,
        # '{Classical,Hip-Hop,R&B}' -> ['Classical', 'Hip-Hop', 'R&B']
        "genres": artist_data.genres.strip('{}').split(','),
        "city": artist_data.city,
        "state": artist_data.state,
        "phone": artist_data.phone,
        "website": artist_data.website_link,
        "facebook_link": artist_data.facebook_link,
        "seeking_venue": artist_data.seeking_venue,
        "seeking_description": artist_data.seeking_description,
        "image_link": artist_data.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id).__dict__

    form.name.data = artist['name']
    form.city.data = artist['city']
    form.state.data = artist['state']
    form.phone.data = artist['phone']
    form.image_link.data = artist['image_link']
    form.genres.data = artist['genres']
    form.facebook_link.data = artist['facebook_link']
    form.website_link.data = artist['website_link']
    form.seeking_venue.data = artist['seeking_venue']
    form.seeking_description.data = artist['seeking_description']

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    if form.validate():
        try:
            artist = Artist.query.get(artist_id)

            artist.name = request.form['name']
            artist.city = request.form['city']
            artist.state = request.form['state']
            artist.phone = request.form['phone']
            artist.image_link = request.form['image_link']
            artist.genres = request.form.getlist('genres', type=str)
            artist.facebook_link = request.form['facebook_link']
            artist.website_link = request.form['website_link']
            artist.seeking_venue = "seeking_venue" in request.form
            artist.seeking_description = request.form['seeking_description']

            if ArtistForm(request.form).validate():
                print('YYYYY', flush=True)
            else:
                print('NNNNN', flush=True)

            session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully edited!')
            
        except Exception as e:
            session.rollback()
            print(e, flush=True)
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')

        finally:
            session.close()

        return redirect(url_for('show_artist', artist_id=artist_id))

    else:
        for message in form.errors.items():
            # e.g. ('phone', ['Invalid phone number format.']) -> Invalid phone number format.
            flash(message[1][0], 'warning')

        return redirect(request.referrer)
        

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    if form.validate():
        try:
            new_artist = Artist(
                name = request.form['name'],
                city = request.form['city'],
                state = request.form['state'],
                phone = request.form['phone'],
                genres = request.form.getlist('genres', type=str),
                facebook_link = request.form['facebook_link'],
                image_link = request.form['image_link'],
                website_link = request.form['website_link'],
                seeking_venue = "seeking_venue" in request.form,
                seeking_description = request.form['seeking_description']
            )

            session.add(new_artist)
            session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
            return redirect(url_for('show_artist', artist_id=Artist.query.order_by(Artist.id.desc()).first().id))
            
        except Exception as e:
            session.rollback()
            print(e, flush=True)
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

        finally:
            session.close()

        return render_template('pages/home.html')

    else:
        for message in form.errors.items():
            # e.g. ('phone', ['Invalid phone number format.']) -> Invalid phone number format.
            flash(message[1][0], 'warning')

        return redirect(request.referrer)


@app.route('/artists/<artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        artist_name = artist.name
        session.delete(artist)
        session.commit()
        flash('Artist ' + artist_name + ' was successfully deleted!')

    except Exception as e:
        session.rollback()
        print(e, flush=True)
        flash('An error occurred. The artist (ID: ' + artist_id + ') could not be deleted.')
    
    finally:
        session.close()
    
    return jsonify({'success': True})


#    Shows
#    ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = session.query(
        Venue.id,
        Venue.name,
        Artist.id,
        Artist.name,
        Artist.image_link,
        Show.start_time
    ).join(Artist).join(Venue).all()

    data = []
    for i in shows:
        data.append({
            'venue_id': i[0],
            'venue_name': i[1],
            'artist_id': i[2],
            'artist_name': i[3],
            'artist_image_link': i[4],
            'start_time': i[5].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        })
    print(data, flush=True)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    if form.validate():
        try:
            new_show = Show(
                artist_id = request.form['artist_id'],
                venue_id = request.form['venue_id'],
                start_time = request.form['start_time'],
            )

            session.add(new_show)
            session.commit()
            flash('Show was successfully listed!')
            return redirect(url_for('shows'))
            
        except Exception as e:
            session.rollback()
            flash('An error occurred. Show could not be listed.', 'error')

        finally:
            session.close()

        return render_template('pages/home.html')
        

    else:
        for message in form.errors.items():
            # e.g. ('phone', ['Invalid phone number format.']) -> Invalid phone number format.
            flash(message[1][0], 'warning')

        return redirect(request.referrer)


@app.errorhandler(404)
def not_found_error(error):
        return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
        return render_template('errors/500.html'), 500


if not app.debug:
        file_handler = FileHandler('error.log')
        file_handler.setFormatter(
                Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        )
        app.logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
        app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
'''
