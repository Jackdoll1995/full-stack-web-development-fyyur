from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from sqlalchemy import func
from werkzeug.exceptions import abort

from db import session
from forms import *
from models.artist import Artist
from models.show import Show
from models.venue import Venue

bp = Blueprint('venue', __name__)


@bp.route('/venues')
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


@bp.route('/venues/search', methods=['POST'])
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


@bp.route('/venues/<int:venue_id>')
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


@bp.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@bp.route('/venues/create', methods=['POST'])
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


@bp.route('/venues/<venue_id>/delete', methods=['DELETE'])
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


@bp.route('/venues/<int:venue_id>/edit', methods=['GET'])
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


@bp.route('/venues/<int:venue_id>/edit', methods=['POST'])
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

        return redirect(url_for('venue.show_venue', venue_id=venue_id))

    else:
        for message in form.errors.items():
            # e.g. ('phone', ['Invalid phone number format.']) -> Invalid phone number format.
            flash(message[1][0], 'warning')

        return redirect(request.referrer)
