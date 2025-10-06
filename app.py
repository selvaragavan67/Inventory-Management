from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------ MODELS ------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class ProductMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    from_location = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    to_location = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ ROUTES ------------------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- PRODUCTS ----------
@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name']
    db.session.add(Product(name=name))
    db.session.commit()
    return redirect(url_for('products'))

# ---------- LOCATIONS ----------
@app.route('/locations')
def locations():
    all_locations = Location.query.all()
    return render_template('locations.html', locations=all_locations)

@app.route('/add_location', methods=['POST'])
def add_location():
    name = request.form['name']
    db.session.add(Location(name=name))
    db.session.commit()
    return redirect(url_for('locations'))

# ---------- PRODUCT MOVEMENTS ----------
@app.route('/movements')
def movements():
    all_movements = ProductMovement.query.all()
    products = Product.query.all()
    locations = Location.query.all()
    return render_template('movements.html', movements=all_movements,
                           products=products, locations=locations)

@app.route('/add_movement', methods=['POST'])
def add_movement():
    product_id = request.form['product']
    from_location = request.form.get('from_location') or None
    to_location = request.form.get('to_location') or None
    quantity = int(request.form['quantity'])
    movement = ProductMovement(product_id=product_id,
                               from_location=from_location,
                               to_location=to_location,
                               quantity=quantity)
    db.session.add(movement)
    db.session.commit()
    return redirect(url_for('movements'))

# ---------- REPORT ----------
@app.route('/report')
def report():
    query = text('''
        SELECT p.name AS product, l.name AS location,
        COALESCE(SUM(CASE WHEN pm.to_location = l.id THEN pm.quantity ELSE 0 END), 0) -
        COALESCE(SUM(CASE WHEN pm.from_location = l.id THEN pm.quantity ELSE 0 END), 0) AS balance
        FROM product p
        CROSS JOIN location l
        LEFT JOIN product_movement pm ON pm.product_id = p.id
        GROUP BY p.name, l.name
        HAVING balance != 0
        ORDER BY p.name, l.name;
    ''')
    data = db.session.execute(query).fetchall()
    return render_template('report.html', data=data)

# ---------- RUN ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
