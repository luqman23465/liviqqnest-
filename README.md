# LiviqNest - Property Management Application

LiviqNest is a Flask-based web application for managing real estate property listings. It features a public interface to view properties and an admin panel for property management, secured with JWT authentication and a database for persistent storage.

## Features

*   Public listing of properties with filtering (For Sale/To Rent) and search.
*   Admin panel (`/admin`) for CRUD (Create, Read, Update, Delete) operations on properties.
*   Secure admin authentication using JWTs stored in HTTP-only cookies.
*   Initial admin user setup via console prompts on first run.
*   Passwords stored securely (hashed and salted using Werkzeug).
*   SQLite database for data persistence.
*   3D house model viewer on the main page (using Three.js).
*   Responsive design using Tailwind CSS for the main page.

## Setup and Usage (Linux & macOS)

### Prerequisites

*   **Python 3.8+**: Ensure Python 3 is installed. You can check with `python3 --version`.
*   **pip**: Python's package installer. Usually comes with Python. Check with `pip3 --version`.
*   **Git**: For cloning the repository (if applicable).

### 1. Clone the Repository (if applicable)

If you have the project files in a Git repository, clone it:
```bash
git clone <repository_url>
cd <repository_directory_name> # e.g., liviqnest
```
If you have the files directly, navigate to the project's root directory.

### 2. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
```
Your terminal prompt should now indicate that you are in the `(venv)` environment.

### 3. Install Dependencies

Install the required Python packages using `pip` and the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 4. Initialize Database and Create Admin User

The application is designed to help you set up the database and the first admin user when you run it for the first time if the database file (`properties.db`) doesn't exist or if the admin user table is empty.

*   **First time running the application:**
    When you run `python app.py` for the first time (and `properties.db` is not yet created or is empty of an admin user), the script will:
    1.  Create the `properties.db` file.
    2.  Create the necessary tables (`properties`, `admin_users`) as defined in `schema.sql`.
    3.  Prompt you in the terminal to create an admin user:
        ```
        No admin user found. Please create one.
        Enter admin username: <your_desired_admin_username>
        Enter admin password: <your_desired_password> (input will be hidden)
        Confirm admin password: <re-enter_your_password>
        ```
    4.  Upon successful creation, it will print a confirmation message like "Admin user '<username>' created successfully."

*   **If `properties.db` or `admin_users` table needs manual initialization:**
    You can use the Flask CLI command to initialize the database schema (this will create tables but not the admin user if the table already exists but is empty).
    ```bash
    flask initdb
    ```
    Then, running `python app.py` should trigger the admin user creation prompt if no admin user exists.

### 5. Run the Flask Application

Once the dependencies are installed and the initial admin user is set up (if it was the first run), you can start the Flask development server:

```bash
python app.py
```

You should see output similar to this:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5001
Press CTRL+C to quit
 * Restarting with stat (if debug mode is on and changes are made)
 * Debugger is active!
 * Debugger PIN: ...
```
(The "Database properties.db not found. Initializing..." and admin creation prompts will only appear on the very first run or if `properties.db` is deleted.)

### 6. Access the Application

*   **Main Public Site**: Open your web browser and go to `http://127.0.0.1:5001/`
*   **Admin Panel Login**: Navigate to `http://127.0.0.1:5001/admin/login`
    *   Log in with the admin username and password you created during the setup in step 4.
*   **Admin Dashboard**: After successful login, you will be redirected to `http://127.0.0.1:5001/admin` where you can manage properties.

### Stopping the Application

Press `CTRL+C` in the terminal where the Flask app is running.

### Deactivating the Virtual Environment

When you are done working on the project, you can deactivate the virtual environment:
```bash
deactivate
```

## Project Structure

```
.
├── app.py                # Main Flask application file
├── requirements.txt      # Python dependencies
├── schema.sql            # Database schema definition
├── properties.db         # SQLite database file (created on run)
├── static/               # Static files (CSS, JavaScript, images)
│   ├── style.css
│   └── images/
│       └── ... (property images, placeholders)
├── templates/            # HTML templates
│   ├── index.html        # Main public page
│   ├── admin.html        # Admin dashboard
│   ├── admin_login.html  # Admin login page
│   └── admin_add_edit_property.html # Form for adding/editing properties
└── README.md             # This file
```

## Notes

*   **Debug Mode**: The application runs in debug mode by default (`app.run(debug=True)`). For production, set `debug=False` and use a production-grade WSGI server (e.g., Gunicorn, uWSGI) instead of Flask's built-in development server.
*   **Secret Key**: The `app.secret_key` in `app.py` is hardcoded for development. In a production environment, this should be a strong, random key loaded from an environment variable or a secure configuration file.
*   **HTTPS**: For production, ensure the application is served over HTTPS, especially since authentication (even with HttpOnly cookies) is involved. The `secure=request.is_secure` flag for cookies will then ensure they are only sent over HTTPS.
```
