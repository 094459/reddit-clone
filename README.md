# Reddit Clone in Python

A Reddit-like online forum built with Flask and SQLite, featuring societies (subreddits), posts, comments, and moderation tools. **Oeddit**, the original source project in PHP can be found [here](https://github.com/zethon/oeddit)

You can read how this repo came to be by checking out this blog post, [From PHP to Python with the help of Amazon Q Developer](https://community.aws/content/2uMzlDBb6QvKe0pjBU1bbNt3V61/from-php-to-python-porting-a-reddit-clone-with-the-help-of-amazon-q-developer?trk=fd6bb27a-13b0-4286-8269-c7b1cfaa29f0&sc_channel=el)

## Features
- Societies (Subreddits)
- Posts and Comments
- Voting system
- User management
- Moderation tools
- Admin dashboard
- Private messaging

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/oeddit.git
cd oeddit
```

2. Create a virtual environment and activate it
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`
```bash
cp .env.example .env
# Edit .env with your secret key
```

5. Initialize and seed the database
```bash
python create_db.py
```

6. Run the application
```bash
flask run
```

## Default Login
- Admin: adeel/123
- Test Users: user1/password1, user2/password2, etc. (up to user5)

## Project Structure
- `app.py` - Main application file
- `models.py` - Database models
- `forms.py` - Form definitions
- `routes/` - Route handlers organized by feature
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)
- `create_db.py` - Database initialization and seeding script

## Technologies Used
- Python 3.9+
- Flask - Web framework
- Flask-SQLAlchemy - ORM for database operations
- Flask-Login - User authentication
- Flask-WTF - Form handling
- SQLite - Database
- Bootstrap - Frontend framework

## Development

To reset the database:
1. Delete the `oeddit.db` file
2. Run `python create_db.py` to create and seed a new database

## License
See the LICENSE file for details.
