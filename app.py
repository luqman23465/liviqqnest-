import sqlite3
import os
import jwt # For JWT encoding/decoding
from datetime import datetime, timedelta, timezone # For JWT expiration
from flask import Flask, jsonify, request, render_template, redirect, url_for, g, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import getpass # For securely getting password input from console

app = Flask(__name__)
app.secret_key = 'dev_secret_key_liviqnest_001' # IMPORTANT: Change this in production!
DATABASE = 'properties.db'

# Admin credentials will be removed and managed via DB
# ADMIN_USERNAME = 'admin'
# ADMIN_PASSWORD = 'password123'


# --- Database Utility Functions ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        print("Initialized the database.")

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# Call this function once to create your schema, e.g., from a Python shell or a CLI command
# For development, we can call it if the DB file doesn't exist or when app starts.
# However, for production, this should be a separate setup step.
# For now, let's add a CLI command to initialize it.
@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

# --- Main Page Route ---
@app.route('/')
def index_page():
    return render_template('index.html')

# --- API Endpoints (Modified for SQLite) ---

@app.route('/api/properties', methods=['GET'])
def get_properties_api():
    properties = query_db('SELECT * FROM properties')
    return jsonify([dict(p) for p in properties])

@app.route('/api/properties/<int:property_id>', methods=['GET'])
def get_property_api(property_id):
    property_item = query_db('SELECT * FROM properties WHERE id = ?', [property_id], one=True)
    if property_item:
        return jsonify(dict(property_item))
    return jsonify({"message": "Property not found"}), 404

@app.route('/api/properties', methods=['POST'])
def add_property_api():
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'description', 'price', 'status']):
        return jsonify({"message": "Missing data"}), 400

    # Default image if not provided - note: ID is not known before insert
    # We'll handle default image naming slightly differently or let it be null/empty
    image_url = data.get('image_url', '')

    try:
        db = get_db()
        cursor = db.execute('INSERT INTO properties (name, description, price, status, image_url) VALUES (?, ?, ?, ?, ?)',
                            [data['name'], data['description'], data['price'], data['status'], image_url])
        db.commit()
        new_property_id = cursor.lastrowid

        # Optionally create a placeholder if image_url was generated/defaulted and is filename-based
        # For now, we assume image_url is either provided or empty.
        # If we were to generate like default_<id>.jpg, we'd do it here after getting the ID.

        new_property = query_db('SELECT * FROM properties WHERE id = ?', [new_property_id], one=True)
        return jsonify(dict(new_property)), 201
    except sqlite3.Error as e:
        return jsonify({"message": "Database error", "error": str(e)}), 500


@app.route('/api/properties/<int:property_id>', methods=['PUT'])
def update_property_api(property_id):
    property_item = query_db('SELECT * FROM properties WHERE id = ?', [property_id], one=True)
    if not property_item:
        return jsonify({"message": "Property not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    # Build query dynamically based on provided fields
    update_fields = {}
    for key in ['name', 'description', 'price', 'status', 'image_url']:
        if key in data:
            update_fields[key] = data[key]

    if not update_fields:
         return jsonify({"message": "No fields to update provided"}), 400

    set_clause = ", ".join([f"{key} = ?" for key in update_fields.keys()])
    values = list(update_fields.values())
    values.append(property_id)

    try:
        db = get_db()
        db.execute(f'UPDATE properties SET {set_clause} WHERE id = ?', values)
        db.commit()
        updated_property = query_db('SELECT * FROM properties WHERE id = ?', [property_id], one=True)
        return jsonify(dict(updated_property))
    except sqlite3.Error as e:
        return jsonify({"message": "Database error", "error": str(e)}), 500


@app.route('/api/properties/<int:property_id>', methods=['DELETE'])
def delete_property_api(property_id):
    property_item = query_db('SELECT * FROM properties WHERE id = ?', [property_id], one=True)
    if not property_item:
        return jsonify({"message": "Property not found"}), 404
    try:
        db = get_db()
        db.execute('DELETE FROM properties WHERE id = ?', [property_id])
        db.commit()
        return jsonify({"message": "Property deleted"}), 200
    except sqlite3.Error as e:
        return jsonify({"message": "Database error", "error": str(e)}), 500

# --- Admin Authentication Routes ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('admin_login.html')

        user = query_db("SELECT * FROM admin_users WHERE username = ?", [username], one=True)

        if user and check_password_hash(user['password_hash'], password):
            # Create JWT token
            payload = {
                'user': user['username'], # Use username from DB
                'exp': datetime.now(timezone.utc) + timedelta(hours=1)  # Token expires in 1 hour
            }
            try:
                token = jwt.encode(payload, app.secret_key, algorithm='HS256')
                response = make_response(redirect(url_for('admin_dashboard')))
                response.set_cookie('admin_jwt_token', token, httponly=True, secure=request.is_secure, samesite='Lax', max_age=3600) # Max age 1 hour
                flash('Login successful!', 'success')
                return response
            except Exception as e:
                flash(f'Error generating token: {str(e)}', 'error')
                # Log the exception e
                print(f"Token generation error: {e}") # For server logs
        else:
            flash('Invalid username or password.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    flash('You have been logged out.', 'info')
    response = make_response(redirect(url_for('admin_login')))
    response.set_cookie('admin_jwt_token', '', expires=0, httponly=True, secure=request.is_secure, samesite='Lax') # Clear the cookie
    return response

# --- Admin Web Interface Routes (Modified for SQLite & Auth) ---
# Decorator to protect admin routes
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('admin_jwt_token')
        if not token:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin_login'))
        try:
            # Decode the token, this will also verify expiration and signature
            payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            # You could add more checks here, e.g., if payload['user'] is a valid admin
            g.admin_user = payload['user'] # Optionally store user info in g for access in route
        except jwt.ExpiredSignatureError:
            flash('Your session has expired. Please log in again.', 'error')
            response = make_response(redirect(url_for('admin_login')))
            response.set_cookie('admin_jwt_token', '', expires=0) # Clear the expired cookie
            return response
        except jwt.InvalidTokenError:
            flash('Invalid token. Please log in again.', 'error')
            response = make_response(redirect(url_for('admin_login')))
            response.set_cookie('admin_jwt_token', '', expires=0) # Clear the invalid cookie
            return response
        except Exception as e: # Catch any other decoding errors
            flash(f'Login error: {str(e)}. Please log in again.', 'error')
            print(f"JWT decoding error: {e}") # For server logs
            response = make_response(redirect(url_for('admin_login')))
            response.set_cookie('admin_jwt_token', '', expires=0) # Clear the cookie
            return response

        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    properties = query_db('SELECT * FROM properties ORDER BY id DESC')
    return render_template('admin.html', properties=[dict(p) for p in properties])

@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add_property():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        status = request.form['status']
        image_url = request.form.get('image_url', '') # Default to empty string if not provided

        if not all([name, description, price, status]):
            return "Error: Missing form data", 400 # Consider flashing messages

        try:
            db = get_db()
            cursor = db.execute('INSERT INTO properties (name, description, price, status, image_url) VALUES (?, ?, ?, ?, ?)',
                                [name, description, float(price), status, image_url])
            db.commit()
            new_id = cursor.lastrowid
            # If image_url was empty and we want a default like 'static/images/default_<id>.jpg':
            if not image_url:
                default_image_url = f"static/images/default_{new_id}.jpg"
                db.execute('UPDATE properties SET image_url = ? WHERE id = ?', [default_image_url, new_id])
                db.commit()
                # Optionally create the placeholder file
                try:
                    with open(default_image_url, 'w') as f:
                        f.write(f"Placeholder for {default_image_url}")
                except Exception as e:
                    print(f"Could not create placeholder image {default_image_url}: {e}")

            return redirect(url_for('admin_dashboard'))
        except sqlite3.Error as e:
            # Log error, flash message to user
            print(f"Database error on admin add: {e}")
            return "Error adding property to database", 500

    return render_template('admin_add_edit_property.html', form_action='Add', property_item={})

@app.route('/admin/edit/<int:property_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_property(property_id):
    property_item_dict = None
    if request.method == 'GET':
        property_item = query_db('SELECT * FROM properties WHERE id = ?', [property_id], one=True)
        if not property_item:
            return "Property not found", 404
        property_item_dict = dict(property_item)

    if request.method == 'POST':
        # Fetch current item to compare image_url for default generation
        current_item = query_db('SELECT * FROM properties WHERE id = ?', [property_id], one=True)
        if not current_item:
             return "Property not found for update", 404

        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        status = request.form['status']
        image_url = request.form.get('image_url', '') # Default to empty string if not provided

        # If image_url is empty after submission, and it was previously a default, regenerate default.
        # Or, if it's empty and wasn't a default, it means user wants to clear it or use a new default.
        if not image_url:
            image_url = f"static/images/default_{property_id}.jpg"
            # Optionally create the placeholder file if it doesn't exist or if we want to ensure it's there
            if not os.path.exists(image_url):
                 try:
                    with open(image_url, 'w') as f:
                        f.write(f"Placeholder for {image_url}")
                 except Exception as e:
                    print(f"Could not create placeholder image {image_url}: {e}")

        try:
            db = get_db()
            db.execute('UPDATE properties SET name = ?, description = ?, price = ?, status = ?, image_url = ? WHERE id = ?',
                       [name, description, price, status, image_url, property_id])
            db.commit()
            return redirect(url_for('admin_dashboard'))
        except sqlite3.Error as e:
            print(f"Database error on admin edit: {e}")
            return "Error updating property in database", 500

    # For GET request, property_item_dict is already fetched
    return render_template('admin_add_edit_property.html', form_action='Edit', property_item=property_item_dict)


@app.route('/admin/delete/<int:property_id>', methods=['POST'])
@admin_required
def admin_delete_property(property_id):
    # Check if property exists before deleting (optional, but good practice)
    property_item = query_db('SELECT * FROM properties WHERE id = ?', [property_id], one=True)
    if not property_item:
        # Optionally flash a message "Property already deleted or not found"
        return redirect(url_for('admin_dashboard'))
    try:
        db = get_db()
        db.execute('DELETE FROM properties WHERE id = ?', [property_id])
        db.commit()
        # Optionally delete associated image file if it was a default one
        # image_to_delete = f"static/images/default_{property_id}.jpg"
        # if os.path.exists(image_to_delete) and property_item['image_url'] == image_to_delete:
        #    os.remove(image_to_delete)
        return redirect(url_for('admin_dashboard'))
    except sqlite3.Error as e:
        print(f"Database error on admin delete: {e}")
        return "Error deleting property from database", 500


if __name__ == '__main__':
    # Ensure DB is initialized (for development convenience)
    # A better approach for prod is the CLI 'flask initdb'
    import os
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found. Initializing...")
        init_db() # This needs to be callable without active request context if run here
                  # Or simply run `flask initdb` manually first.
                  # For simplicity here, we assume manual `flask initdb` or it's handled by `get_db` implicitly creating the file.
                  # The `init_db` function as written needs an app_context.
                  # A common pattern is to check and init within the first request or before first request.

    # To ensure `init_db` can be called if the DB doesn't exist when the app starts:
    # We can't call init_db() directly here as it needs app_context.
    # One way:
    with app.app_context():
        if not os.path.exists(DATABASE):
            init_db() # Initialize DB if it doesn't exist
        # You could also add some default data here if the DB is newly created and empty
        # c = get_db().cursor()
        # if c.execute("SELECT COUNT(*) FROM properties").fetchone()[0] == 0:
        #    print("Adding initial data...")
        #    get_db().executemany("INSERT INTO properties (name, description, price, status, image_url) VALUES (?,?,?,?,?)", [
        #        ("Luxury Villa", "A beautiful villa with a sea view.", 1200000, "sale", "static/images/villa.jpg"),
        #        ("Cozy Apartment", "A cozy apartment in the city center.", 2500, "rent", "static/images/apartment.jpg")
        #    ])
        #    get_db().commit()

        create_admin_user_if_not_exists()

    app.run(debug=True, port=5001)

# --- Admin User Setup ---
def create_admin_user_if_not_exists():
    with app.app_context(): # Ensure we have an app context for get_db()
        db = get_db()
        cur = db.execute("SELECT COUNT(*) FROM admin_users")
        admin_exists = cur.fetchone()[0] > 0
        cur.close()

        if not admin_exists:
            print("No admin user found. Please create one.")
            while True:
                username = input("Enter admin username: ").strip()
                if not username:
                    print("Username cannot be empty.")
                    continue
                # Check if username already exists (shouldn't happen if table is empty, but good practice)
                # For this initial setup, we assume it won't if admin_exists is false.
                break

            while True:
                password = getpass.getpass("Enter admin password: ")
                if not password:
                    print("Password cannot be empty.")
                    continue
                password_confirm = getpass.getpass("Confirm admin password: ")
                if password == password_confirm:
                    break
                else:
                    print("Passwords do not match. Please try again.")

            password_hash = generate_password_hash(password)
            try:
                db.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)", (username, password_hash))
                db.commit()
                print(f"Admin user '{username}' created successfully.")
            except sqlite3.IntegrityError: # Should not happen if initial check is robust
                print(f"Error: Admin user '{username}' may already exist or another integrity constraint failed.")
            except Exception as e:
                print(f"An error occurred while creating admin user: {e}")
        else:
            print("Admin user already exists.")
