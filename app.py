from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import logging

app = Flask(__name__)

# Configure CORS to allow requests from your frontend
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'foodwaste.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT configuration
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-this'  # Change this in production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Add this after app initialization
logging.basicConfig(level=logging.DEBUG)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

class FoodListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Float, nullable=False)
    quantity_unit = db.Column(db.String(20), nullable=False)
    expiry_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # "AVAILABLE", "RESERVED", "COLLECTED"
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Subscription Model
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False)  # 'basic', 'premium', 'enterprise'
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'active', 'expired', 'cancelled'
    amount_paid = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)

# Delivery Model
class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_listing_id = db.Column(db.Integer, db.ForeignKey('food_listing.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pickup_location = db.Column(db.String(200), nullable=False)
    delivery_location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'pending', 'in_transit', 'delivered'
    current_latitude = db.Column(db.Float)
    current_longitude = db.Column(db.Float)
    last_updated = db.Column(db.DateTime)

# Routes
@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/subscribe')
def subscribe_page():
    return render_template('subscribe.html')

@app.route('/tracking')
def tracking_page():
    return render_template('tracking.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already registered'}), 400
        
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            first_name=data['firstName'],
            last_name=data['lastName'],
            email=data['email'],
            password=hashed_password,
            user_type=data['userType'],
            address=data['address'],
            phone=data['phone']
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Registration successful'}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password, data['password']):
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'token': access_token,
                'user': {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}",
                    'email': user.email,
                    'userType': user.user_type
                }
            }), 200
        
        return jsonify({'message': 'Invalid email or password'}), 401
    
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Protected route example
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({'message': f'Hello {user.first_name}!'}), 200

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    
    try:
        # Verify user exists and is authenticated
        user = User.query.filter_by(id=data['userId']).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Calculate subscription dates
        start_date = datetime.now()
        if data['plan_type'] == 'monthly':
            end_date = start_date + timedelta(days=30)
        elif data['plan_type'] == 'yearly':
            end_date = start_date + timedelta(days=365)
        else:
            return jsonify({'message': 'Invalid plan type'}), 400

        # Create new subscription
        new_subscription = Subscription(
            user_id=data['userId'],
            plan_type=data['plan_type'],
            start_date=start_date,
            end_date=end_date,
            status='active',
            amount_paid=data['amount'],
            payment_method=data['payment_method']
        )

        db.session.add(new_subscription)
        db.session.commit()

        return jsonify({
            'message': 'Subscription successful',
            'subscription': {
                'plan_type': data['plan_type'],
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Subscription failed', 'error': str(e)}), 500

@app.route('/update-location', methods=['POST'])
def update_location():
    data = request.json
    try:
        delivery = Delivery.query.filter_by(id=data['deliveryId']).first()
        if not delivery:
            return jsonify({'message': 'Delivery not found'}), 404

        delivery.current_latitude = data['latitude']
        delivery.current_longitude = data['longitude']
        delivery.last_updated = datetime.now()

        db.session.commit()
        return jsonify({'message': 'Location updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update location', 'error': str(e)}), 500

@app.route('/get-delivery-location/<delivery_id>', methods=['GET'])
def get_delivery_location(delivery_id):
    try:
        delivery = Delivery.query.get(delivery_id)
        if not delivery:
            return jsonify({'message': 'Delivery not found'}), 404

        return jsonify({
            'latitude': delivery.current_latitude,
            'longitude': delivery.current_longitude,
            'last_updated': delivery.last_updated.isoformat(),
            'status': delivery.status
        }), 200

    except Exception as e:
        return jsonify({'message': 'Error fetching location', 'error': str(e)}), 500

@app.route('/donate')
def donate_page():
    return render_template('donate.html')

@app.route('/api/donate', methods=['POST'])
@jwt_required()
def donate():
    try:
        data = request.json
        user_id = get_jwt_identity()
        
        new_listing = FoodListing(
            restaurant_id=user_id,
            food_name=data['foodName'],
            description=data['description'],
            quantity=float(data['quantity']),
            quantity_unit=data['unit'],
            expiry_time=datetime.fromisoformat(data['expiryDate'].replace('Z', '+00:00')),
            status="AVAILABLE"
        )
        
        db.session.add(new_listing)
        db.session.commit()
        
        return jsonify({'message': 'Donation listed successfully'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/home')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
    
    app.run(debug=True, port=5000) 