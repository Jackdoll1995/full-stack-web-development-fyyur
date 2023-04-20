import dateutil.parser
import babel
import logging

from datetime import datetime
from db import db
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_moment import Moment
from logging import Formatter, FileHandler
from forms import *

from services import artist, home, show, venue

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

moment = Moment()
migrate = Migrate()

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


#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    moment.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    app.jinja_env.filters['datetime'] = format_datetime

    app.register_blueprint(home.bp)
    app.add_url_rule('/', endpoint='index')

    app.register_blueprint(artist.bp)
    app.add_url_rule('/artists', endpoint='artists')

    app.register_blueprint(show.bp)
    app.add_url_rule('/shows', endpoint='shows')

    app.register_blueprint(venue.bp)
    app.add_url_rule('/venues', endpoint='venues')

    if not app.debug:
        file_handler = FileHandler('error.log')
        file_handler.setFormatter(
                Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        )
        app.logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.info('errors')

    @app.errorhandler(404)
    def not_found_error(error):
            return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(error):
            return render_template('errors/500.html'), 500

    return app


# Default port:
if __name__ == '__main__':
        app = create_app()
        app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
'''
