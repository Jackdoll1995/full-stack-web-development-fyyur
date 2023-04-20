from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from db import session
from forms import *
from models.artist import Artist
from models.show import Show
from models.venue import Venue

bp = Blueprint('show', __name__)


@bp.route('/shows')
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

    return render_template('pages/shows.html', shows=data)


@bp.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@bp.route('/shows/create', methods=['POST'])
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
