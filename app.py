#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable = False)
    genres = db.Column("genres", db.ARRAY(db.String(120)), nullable = False)
    city = db.Column(db.String(120), nullable = False)
    state = db.Column(db.String(120), nullable = False)
    address = db.Column(db.String(120), nullable = False)
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean(), default = False)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref='venue')


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable = False)
    genres = db.Column("genres", db.ARRAY(db.String(120)), nullable = False)
    city = db.Column(db.String(120), nullable = False)
    state = db.Column(db.String(120), nullable = False)
    phone = db.Column(db.String(120), default = '')
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean(), default = False)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref = 'artist')


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key = True)
    start_time = db.Column(db.DateTime, nullable = False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable = False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable = False)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

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
  data = []
  venues = Venue.query.all()
  
  areas = list()
  for venue in venues:
    area = (venue.city, venue.state)
    if area not in areas:
      areas.append(area)

  for area in areas:
    data.append({
      "city": area[0],
      "state": area[1],
      "venues": []
    })

  for venue in venues:
    area = (venue.city, venue.state)
    position = areas.index(area)
    data[position]['venues'].append({
      "id": venue.id,
      "name": venue.name,
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  
  # ref: https://stackoverflow.com/a/20367821
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  data = []
  if venues:
    for venue in venues:
      venue_data = {
        "id": venue.id,
        "name": venue.name
      }
      data.append(venue_data)
  
  response={
    "count": len(venues),
    "data": data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  data = {}
  shows = Show.query.filter_by(venue_id = venue_id).all()
  past_shows = []
  upcoming_shows = []

  if shows:
    for show in shows:
      artist = show.artist
      start_time = show.start_time
      details = {
        "artist_id": show.venue_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(start_time)
      }

      if start_time <= datetime.now():
        past_shows.append(details)
      else:
        upcoming_shows.append(details)

    # Add artist to data as dictionary
    venue = shows[0].venue
    data.update(vars(venue))
  
  else:
    # Add artist to data as dictionary
    venue = Venue.query.get(venue_id)
    data.update(vars(venue))

  data.update({
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  })  
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  success = True

  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  address = request.form['address']
  phone = request.form['phone']
  genres = request.form.getlist('genres')
  facebook_link = request.form['facebook_link']

  try:
    venue = Venue(name = name, city = city, state = state, address = address,
                  phone = phone, genres = genres, facebook_link = facebook_link)

    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + name + ' was successfully listed!')

  except:
    db.session.rollback()
    success = False
    print(sys.exc_info())
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  
  finally:
    db.session.close()

  if success:
    return redirect(url_for('index'))
  else:
    return render_template('forms/new_venue.html', form = ArtistForm())


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  success = True
  venue = Venue.query.get(venue_id)

  try:
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully deleted!')

  except:
    db.session.rollback()
    success = False
    print(sys.exc_info())
    flash('An error occurred. Venue ' + venue.name + ' could not be deleted.')

  finally:
    db.session.close()

  if success:
    return redirect(url_for('venues'))
  else:
    return redirect(url_for('delete_venue', venue_id = venue_id))

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  return render_template('pages/artists.html', artists=artists)
  
@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  
  # ref: https://stackoverflow.com/a/20367821
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  data = []
  if artists:
    for artist in artists:
      artist_data = {
        "id": artist.id,
        "name": artist.name
      }
      data.append(artist_data)
  
  response={
    "count": len(artists),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  data = {}
  shows = Show.query.filter_by(artist_id = artist_id).all()
  
  past_shows = []
  upcoming_shows = []

  if shows:
    for show in shows:
      venue = show.venue
      start_time = show.start_time
      details = {
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": str(start_time)
      }

      if start_time <= datetime.now():
        past_shows.append(details)
      else:
        upcoming_shows.append(details)
    
    # Add artist to data as dictionary
    artist = shows[0].artist
    data.update(vars(artist))
  
  else: 
    # Add artist to data as dictionary
    artist = Artist.query.get(artist_id)
    data.update(vars(artist))

  data.update({
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    })

  return render_template('pages/show_artist.html', artist=data)
  

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.image_link.data = artist.image_link
  form.genres.data = artist.genres
  form.facebook_link.data = artist.facebook_link

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  success = True
  artist = Artist.query.get(artist_id)

  artist.name = request.form['name']
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  artist.genres = request.form.getlist('genres')
  artist.facebook_link = request.form['facebook_link']

  try:
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully updated!')

  except:
    db.session.rollback()
    success = False
    print(sys.exc_info())
    flash('An error occurred. Artist ' + artist.name + ' could not be updated.')
  
  finally:
    db.session.close()

  if success:
    return redirect(url_for('show_artist', artist_id = artist_id))
  else:
    return render_template('forms/edit_artist.html', form = ArtistForm(), artist = artist)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.image_link.data = venue.image_link
  form.genres.data = venue.genres
  form.facebook_link.data = venue.facebook_link

  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  success = True
  venue = Venue.query.get(venue_id)

  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.address = request.form['address']
  venue.phone = request.form['phone']
  venue.genres = request.form.getlist('genres')
  venue.facebook_link = request.form['facebook_link']

  try:
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully updated!')

  except:
    db.session.rollback()
    success = False
    print(sys.exc_info())
    flash('An error occurred. Venue ' + venue.name + ' could not be updated.')
  
  finally:
    db.session.close()

  if success:
    return redirect(url_for('show_venue', venue_id = venue_id))
  else:
    return render_template('forms/edit_venue.html', form=VenueForm(), venue=venue)


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  success = True

  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  phone = request.form['phone']
  genres = request.form.getlist('genres')
  facebook_link = request.form['facebook_link']

  try:
    artist = Artist(name = name, city = city, state = state, phone = phone, 
                  genres = genres, facebook_link = facebook_link)

    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + name + ' was successfully listed!')

  except:
    db.session.rollback()
    success = False
    print(sys.exc_info())
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  
  finally:
    db.session.close()

  if success:
    return redirect(url_for('index'))
  else:
    return render_template('forms/new_artist.html', form = ArtistForm())


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = []
  shows = Show.query.all()

  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
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
  success = True

  artist_id = request.form['artist_id']
  venue_id = request.form['venue_id']
  start_time = request.form['start_time']

  try:
    show = Show(artist_id = artist_id, venue_id = venue_id, start_time = start_time)

    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')

  except:
    db.session.rollback()
    success = False
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
  
  finally:
    db.session.close()

  if success:
    return redirect(url_for('index'))
  else:
    return render_template('forms/new_show.html', form = ShowForm())


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
