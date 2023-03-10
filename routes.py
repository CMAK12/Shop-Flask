from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, LoginManager, login_required, current_user
from werkzeug.utils import secure_filename
from flask_login import UserMixin
from config import UPLOAD_FOLDER, SESSION_TYPE, SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from models import db, User, Filters, VideoGame
from flask_restful import Api
import requests
from os import path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_TYPE'] = SESSION_TYPE
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
db.init_app(app)
api = Api(app)
lm = LoginManager()
lm.init_app(app)
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    

@app.route('/cart')
def cart():
    if 'cart' in session:
        cart_items = session['cart']
    else:
        cart_items = []
    return render_template('cart.html', cart_items=cart_items)

@app.route('/cart/add/<int:game_id>')
def add_cart(game_id):
    session.permanent = True
    game = VideoGame.query.filter_by(id=game_id).first()

    if 'cart' not in session:
        session['cart'] = []

    cart_item = session['cart']
    print(cart_item)

    for item in cart_item:
        if item['id'] == game.id:
            item['quantity'] += 1
            item['price'] += game.price
            session.modified = True
            return redirect(url_for('cart'))

    else:
        cart_item.append({'id': game.id, 'name': game.name, 'price': game.price, 'quantity': 1, 'image': game.image_url, 'category_id': game.category_id})
        session['cart'] = cart_item 

    return redirect(url_for('cart'))


@app.route('/delete_cart/<int:game_id>')
def delete_cart(game_id):
    cart_items = session.get('cart')

    for item in cart_items:
        if item['id'] == game_id:
            cart_items.remove(item)

    session['cart'] = cart_items
    return redirect(url_for('cart'))


@app.route('/remove_cart/<int:game_id>')
def remove_cart(game_id):
    cart_items = session.get('cart')

    for item in cart_items:
        if item['id'] == game_id:
            if item['quantity'] > 1:
                item['quantity'] -= 1
            else:
                cart_items.remove(item)

    session['cart'] = cart_items
    return redirect(url_for('cart'))
    

@app.route('/category/<int:category_id>')
def category_list(category_id):
    games = VideoGame.query.filter_by(category_id=category_id)
    return render_template('category_game.html', games=games)
    

@app.route('/category/<int:category_id>/<int:product_id>')
def product(category_id, product_id):
    game = VideoGame.query.filter_by(category_id=category_id, id=product_id).first()
    return render_template('product.html', game=game)


@app.route('/delete_product/<int:product_id>')
@login_required
def delete_product(product_id):
    game = VideoGame.query.filter_by(id=product_id).first()
    try:
        db.session.delete(game)
        db.session.commit()
        flash('Game succesfully deleted')
        return redirect('home')
    except Exception:
        flash('This product cannot be deleted')
        return redirect('home')


@app.route('/add_category', methods=['POST', 'GET'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        slug = name.lower()
        if name and slug:
            category = Filters(name_filter=name, slug=slug)
            db.session.add(category)
            db.session.commit()
        else:
            flash('Your fields clear')
    return render_template('add_category.html')


@app.route('/edit_game/<int:product_id>', methods=['POST', 'GET'])
@login_required
def edit_game(product_id):
    filters = Filters.query.all()
    game = VideoGame.query.filter_by(id=product_id).first()
    if request.method == 'POST':
        game.name = request.form.get('name_of_game')
        game.release_date = request.form.get('release_date')
        game.price = request.form.get('price')
        game.about_game = request.form.get('about_game')
        category_id = request.form.get('category')
        game.category_id = int(category_id)
        image_file = request.files.get('game_image')
        if image_file:
            image_path = game.image_url(image_file)
            game.image_url = image_path
        try:
            db.session.commit()
            return redirect(url_for('home'))
        except Exception:
            return '<h1>Page not found</h1>'


    return render_template('edit_game.html', game=game, filters=filters)


@app.route('/add_game', methods=['POST', 'GET'])
@login_required
def add_game():
    filters = Filters.query.all()
    if request.method == 'POST':
        name = request.form.get('name_of_game')
        date = request.form.get('release_date')
        price = request.form.get('price')
        about_game = request.form.get('about_game')
        category = request.form.get('category')
        image_file = request.files['game_image']

        if image_file:
            filename = secure_filename(image_file.filename)
            filepath = path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)

        else:
            filepath = ''

        new_game = VideoGame(name=name, about_game=about_game, date=date, image_url=filepath, price=price, category_id=category)
        db.session.add(new_game)
        db.session.commit()
    return render_template('add_game.html', filters=filters)


@app.route('/user_list')
def users():
    user = User.query.filter_by(admin_status=False)
    return render_template('user_list.html', user=user)


@app.route('/user_list/edit/<int:user_id>', methods=['POST', 'GET'])
def edit_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if request.method == 'POST':
        user.firstname = request.form.get('firstname')
        user.lastname = request.form.get('lastname')
        user.login = request.form.get('login')
        admin_status = request.form.get('admin_status')
        user.admin_status = bool(int(admin_status))
        try:
            db.session.commit()
            return redirect(url_for('home'))
        except Exception:
            return redirect(url_for('home'))
    return render_template('edit_user.html', user=user)


@app.route('/user_list/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User has been deleted')
        return redirect(url_for('users'))
    except Exception:
        flash('Error')
        return redirect(url_for('home'))


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        login = request.form.get('login')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        user = User.query.filter_by(login=login).first()

        if not user:
            if password == confirm_password:
                user = User(firstname=firstname, lastname=lastname, login=login, password=password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return redirect(url_for('home'))
            else:
                return redirect(url_for('signup'))
        else:
            flash('This login is busy')
        
    return render_template('register.html')


@app.route('/login', methods=['POST', 'GET'])
def logIn():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')

        if login and password:
            user = User.query.filter_by(login=login).first()
            if user and user.password == password:
                login_user(user)

                return redirect(url_for('home'))
            else:
                flash('Login or password is not correct')
        else:
            flash('Please fill login and password fields')
    return render_template('login.html')


@app.route('/logout')
def logOut():
    logout_user()
    return redirect(url_for('home'))


@app.route('/')
def home():
    games = VideoGame.query.all()
    return render_template('home.html', games=games)


@app.route('/about')
def about():
    return render_template('about.html')


@app.context_processor
def settings():
    categories = Filters.query.all()
    exchange_rate = requests.get('https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11').json()[1]
    return {'categories': categories, 'exchange_rate': exchange_rate}


if __name__ == '__main__':
    app.run(debug=True)