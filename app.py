#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate

from forms import *
import sys
from models import Show, Venue, Artist, db
from flask_wtf.csrf import CSRFProtect


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:24680@localhost:5432/testfyyur'


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data=[]
    cities = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)

    for city in cities:
        venues_in_city = db.session.query(Venue.id, Venue.name).filter(Venue.city == city[0]).filter(Venue.state == city[1])
        data.append({
          "city": city[0],
          "state": city[1],
          "venues": venues_in_city
        })
    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    venues = db.session.query(Venue).filter(Venue.name.ilike('%' + search_term + '%')).all()
    data = []

    for venue in venues:
        num_upcoming_shows = 0
        shows = db.session.query(Show).filter(Show.venue_id == venue.id)
        for show in shows:
            if (show.start_time > datetime.now()):
                num_upcoming_shows += 1

        data.append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_upcoming_shows
        })

    response={
          "count": len(venues),
          "data": data
      }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = db.session.query(Venue).filter(Venue.id == venue_id).one()

    list_shows = db.session.query(Show).filter(Show.venue_id == venue_id)
    past_shows = []
    upcoming_shows = []

    for show in list_shows:
      artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == show.artist_id).one()
      show_add = {
          "artist_id": show.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": show.start_time.strftime('%m/%d/%Y')
          }

      if (show.start_time < datetime.now()):
          #print(past_shows, file=sys.stderr)
          past_shows.append(show_add)
      else:
          upcoming_shows.append(show_add)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm(request.form)

    venue = Venue(
      name = form.name.data,
      genres = form.genres.data,
      address = form.address.data,
      city = form.city.data,
      state = form.state.data,
      phone = form.phone.data,
      website = form.website_link.data,
      facebook_link = form.facebook_link.data,
      seeking_talent = form.seeking_talent.data,
      seeking_description = form.seeking_description.data,
      image_link = form.image_link.data,
    )
    try:
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + form.name.data + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    except:
        flash('An error occurred. Venue ' + form.name.data + ' could not be added.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        db.session.query(Venue).filter(Venue.id == venue_id).delete()
        db.session.commit()
        flash('Venue was successfully deleted!')
    except:
        flash('An error occurred. Venue could not be deleted.')
    finally:
        db.session.close()
    return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artists = db.session.query(Artist.id, Artist.name)
    data=[]

    for artist in artists:
        data.append({
          "id": artist[0],
          "name": artist[1]
        })
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    artists = db.session.query(Artist).filter(Artist.name.ilike('%' + search_term + '%')).all()
    data = []

    for artist in artists:
        num_upcoming_shows = 0
        shows = db.session.query(Show).filter(Show.artist_id == artist.id)
        for show in shows:
            if(show.start_time > datetime.now()):
                num_upcoming_shows += 1;
        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming_shows
        })
    response={
        "count": len(artists),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = db.session.query(Artist).filter(Artist.id == artist_id).one()

    list_shows = db.session.query(Show).filter(Show.artist_id == artist_id)
    past_shows = []
    upcoming_shows = []

    for show in list_shows:
        venue = db.session.query(Venue.name, Venue.image_link).filter(Venue.id == show.venue_id).one()

        show_add = {
            "venue_id": show.venue_id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": show.start_time.strftime('%m/%d/%Y')
            }

        if (show.start_time < datetime.now()):
            #print(past_shows, file=sys.stderr)
            past_shows.append(show_add)
        else:
            print(show_add, file=sys.stderr)
            upcoming_shows.append(show_add)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
   
    # TODO: populate form with fields from artist with ID <artist_id>
    artist = db.session.query(Artist).filter(Artist.id == artist_id).one()
    form = ArtistForm(name=artist.name, city=artist.city, state=artist.state, phone=artist.phone, image_link=artist.image_link, genres=artist.genres, facebook_link=artist.facebook_link, website_link=artist.website, seeking_venue=artist.seeking_venue, seeking_description=artist.seeking_description)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form)
    if form.validate():
        try:
            artist = db.session.query(Artist).filter(Artist.id == artist_id).one()
            artist.name = request.form['name']
            artist.genres = request.form.getlist('genres', type=str)
            artist.city = request.form['city']
            artist.phone = request.form['phone']
            artist.website = request.form['website_link']
            artist.facebook_link = request.form['facebook_link']
            artist.seeking_talent = 'seeking_venue' in request.form
            artist.seeking_description = request.form['seeking_description']
            artist.image_link = request.form['image_link']
            db.session.commit()
            flash(f"Artist has been added")
        except:
            flash(f"sorry, the artist is not updated", category="error")
            db.session.rollback()
        
        finally:
            db.session.close()
    else: 
        for field, message in form.errors.items():
            flash(f"{str(message)[2:len(str(message))-2]}", category="danger")
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    
    venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
    form = VenueForm(name=venue.name, city=venue.city, state=venue.state, phone=venue.phone, address=venue.address, image_link=venue.image_link, genres=venue.genres, facebook_link=venue.facebook_link, website_link=venue.website, seeking_talent=venue.seeking_talent, seeking_description=venue.seeking_description)
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)
    if form.validate():
        try:
            venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
            venue.name = request.form['name']
            venue.genres = request.form.getlist('genres', type=str)
            venue.city = request.form['city']
            venue.phone = request.form['phone']
            venue.website = request.form['website_link']
            venue.facebook_link = request.form['facebook_link']
            venue.seeking_talent = 'seeking_venue' in request.form
            venue.seeking_description = request.form['seeking_description']
            venue.image_link = request.form['image_link']
            db.session.commit()
            flash(f"Venue has been added")
        except:
            flash(f"sorry, the venue is not updated", category="error")
            db.session.rollback()
        finally:
            db.session.close()
    else: 
        for field, message in form.errors.items():
            flash(f"{str(message)[2:len(str(message))-2]}", category="danger")
    return redirect(url_for('show_venue', venue_id=venue_id))

    
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    form = ArtistForm(request.form)

    artist = Artist(
        name = form.name.data,
        genres = form.genres.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        website = form.website_link.data,
        facebook_link = form.facebook_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data,
        image_link = form.image_link.data,
    )
    try:
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + form.name.data + ' was successfully listed!')
    except:
        flash('An error occurred. Artist ' + form.name.data + 'could not be added')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = []
    shows = db.session.query(Show.artist_id, Show.venue_id, Show.start_time).all()

    for show in shows:
        artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == show[0]).one()
        venue = db.session.query(Venue.name).filter(Venue.id == show[1]).one()
        data.append({
            "venue_id": show[1],
            "venue_name": venue[0],
            "artist_id": show[0],
            "artist_name": artist[0],
            "artist_image_link": artist[1],
            "start_time": str(show[2])
        })

    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)

    show = Show(
        venue_id = form.venue_id.data,
        artist_id = form.artist_id.data,
        start_time = form.start_time.data
    )

    try:
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed')
    except:
        flash('An error occurred. Show could not be added')
    finally:
        db.session.close()
    return render_template('pages/home.html')

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
