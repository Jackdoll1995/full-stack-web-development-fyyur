from datetime import datetime
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, jsonify
)
from sqlalchemy import func
from werkzeug.exceptions import abort

from db import session
from forms import *
from models.artist import Artist
from models.show import Show
from models.venue import Venue

bp = Blueprint('artist', __name__)


@bp.route('/artists')
def artists():
    data = []
    artists = session.query(Artist.id, Artist.name).all()
    for i in artists:
        data.append({
                'id': i[0],
                'name': i[1],
        })

    return render_template('pages/artists.html', artists=data)


@bp.route('/artists/search', methods=['POST'])
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


@bp.route('/artists/<int:artist_id>')
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


@bp.route('/artists/<int:artist_id>/edit', methods=['GET'])
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


@bp.route('/artists/<int:artist_id>/edit', methods=['POST'])
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

        return redirect(url_for('artist.show_artist', artist_id=artist_id))

    else:
        for message in form.errors.items():
            # e.g. ('phone', ['Invalid phone number format.']) -> Invalid phone number format.
            flash(message[1][0], 'warning')

        return redirect(request.referrer)
        

@bp.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@bp.route('/artists/create', methods=['POST'])
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


@bp.route('/artists/<artist_id>/delete', methods=['DELETE'])
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
