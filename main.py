from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
FILE_URI = 'sqlite:///top-movies-database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = FILE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)

MOVIE_API_KEY = '52ef7b0b34a88b44bf57fa2abb91c1c7'
MOVIE_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
MOVIE_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


class Movie(db.Model):
    __tablename__ = 'Movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(500), nullable=False)

    # Optional: this will allow each book object to be identified by its title when printed.
    def __repr__(self):
        return f'<Movie {self.title}>'

if not os.path.isfile('top-movies-database.db'):
# if not os.path.isfile(FILE_URI): #runs everytime as url is wrong
    db.create_all()
    new_movie = Movie(
        title="Phone Booth",
        year=2002,
        description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
        rating=7.3,
        ranking=10,
        review="My favourite character was the caller.",
        img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    )
    db.session.add(new_movie)
    db.session.commit()

    #TO DELETE ALL MOVIES
    # try:
    #     num_rows_deleted = db.session.query(Movie).delete()
    #     db.session.commit()
    # except:
    #     db.session.rollback()

class RateMovieForm(FlaskForm):
    Rating = StringField('Rating', validators=[DataRequired()])
    Review = StringField('Review', validators=[DataRequired()])
    submit = SubmitField('Submit')

class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route("/")
def home():
    all_movies = db.session.query(Movie).all()
    all_movies = Movie.query.order_by(Movie.rating).all()
    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    # print(all_movies)
    return render_template("index.html", movies=all_movies)

@app.route("/edit/<int:num>", methods=["GET","POST"])
def edit(num):
    form = RateMovieForm()
    movie_entry = Movie.query.filter_by(id=num).first()
    if form.validate_on_submit():
        data = form.data
        print(data)
        print(num)
        movie_entry.rating = float(data['Rating'])
        movie_entry.review = data['Review']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form, movie=movie_entry)

@app.route("/alt_edit", methods=["GET","POST"])
def alt_edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie_entry = Movie.query.filter_by(id=movie_id).first()
    if form.validate_on_submit():
        data = form.data
        print(data)
        movie_entry.rating = float(data['Rating'])
        movie_entry.review = data['Review']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('alt_edit.html', form=form, movie=movie_entry)

@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods=["GET","POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.data
        print(movie_title)
        params = {
            'api_key': MOVIE_API_KEY,
            'query': movie_title['title'],
        }
        r = requests.get(MOVIE_SEARCH_URL, params=params)
        search_data = r.json()['results']
        print(search_data)
        return render_template("select.html", search_data=search_data)

    return render_template('add.html', form=form)

@app.route("/select", methods=["GET"])
def select():
    movie_id = request.args.get("id")
    print(movie_id)
    if movie_id:
        params = {
            'api_key': MOVIE_API_KEY,
        }
        NEW_MOVIE_API_URL = f'{MOVIE_INFO_URL}/{movie_id}'
        r = requests.get(NEW_MOVIE_API_URL, params=params)
        search_data = r.json()
        print(search_data)
        new_movie = Movie(
            title=search_data["title"],
            year=search_data["release_date"],
            description=search_data["overview"],
            img_url=f"{MOVIE_IMAGE_URL}{search_data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        movie = Movie.query.filter_by(title=search_data["title"]).first()
        return redirect(url_for('alt_edit', id=movie.id))

if __name__ == '__main__':
    app.run(debug=True)
