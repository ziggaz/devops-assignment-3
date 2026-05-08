from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'elite-car-rental-secret-key-2026'

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'elite_cars.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        brand TEXT NOT NULL,
        year INTEGER NOT NULL,
        price_per_day REAL NOT NULL,
        available INTEGER DEFAULT 1,
        image_url TEXT DEFAULT ''
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS rentals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        car_id INTEGER NOT NULL,
        rental_date TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (car_id) REFERENCES cars(id)
    )''')
    # Seed cars if table is empty
    cursor.execute('SELECT COUNT(*) FROM cars')
    if cursor.fetchone()[0] == 0:
        cars = [
            ('Toyota Camry', 'Toyota', 2024, 45.00),
            ('Honda Civic', 'Honda', 2023, 40.00),
            ('BMW 3 Series', 'BMW', 2024, 85.00),
            ('Mercedes C-Class', 'Mercedes', 2023, 90.00),
            ('Tesla Model 3', 'Tesla', 2024, 75.00),
            ('Ford Mustang', 'Ford', 2024, 70.00),
            ('Audi A4', 'Audi', 2023, 80.00),
            ('Hyundai Sonata', 'Hyundai', 2024, 35.00),
        ]
        cursor.executemany('INSERT INTO cars (name, brand, year, price_per_day) VALUES (?, ?, ?, ?)', cars)
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            flash('Welcome back, ' + user['full_name'] + '!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (full_name, email, username, password) VALUES (?, ?, ?, ?)',
                         (full_name, email, username, password))
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
        conn.close()
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    search = request.args.get('search', '').strip()
    if search:
        cars = conn.execute('SELECT * FROM cars WHERE available = 1 AND (name LIKE ? OR brand LIKE ?)',
                            ('%' + search + '%', '%' + search + '%')).fetchall()
    else:
        cars = conn.execute('SELECT * FROM cars WHERE available = 1').fetchall()
    conn.close()
    return render_template('dashboard.html', cars=cars, search=search)

@app.route('/rent/<int:car_id>')
def rent_car(car_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('INSERT INTO rentals (user_id, car_id) VALUES (?, ?)', (session['user_id'], car_id))
    conn.execute('UPDATE cars SET available = 0 WHERE id = ?', (car_id,))
    conn.commit()
    conn.close()
    flash('Car rented successfully!', 'success')
    return redirect(url_for('my_rentals'))

@app.route('/my-rentals')
def my_rentals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    rentals = conn.execute('''SELECT rentals.id as rental_id, cars.name, cars.brand, cars.year, 
                              cars.price_per_day, rentals.rental_date, rentals.status
                              FROM rentals JOIN cars ON rentals.car_id = cars.id 
                              WHERE rentals.user_id = ? ORDER BY rentals.id DESC''',
                           (session['user_id'],)).fetchall()
    conn.close()
    return render_template('my_rentals.html', rentals=rentals)

@app.route('/return/<int:rental_id>')
def return_car(rental_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    rental = conn.execute('SELECT car_id FROM rentals WHERE id = ? AND user_id = ?', 
                          (rental_id, session['user_id'])).fetchone()
    if rental:
        conn.execute('UPDATE rentals SET status = ? WHERE id = ?', ('returned', rental_id))
        conn.execute('UPDATE cars SET available = 1 WHERE id = ?', (rental['car_id'],))
        conn.commit()
        flash('Car returned successfully!', 'success')
    conn.close()
    return redirect(url_for('my_rentals'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        conn.execute('UPDATE users SET full_name = ?, email = ? WHERE id = ?',
                     (full_name, email, session['user_id']))
        conn.commit()
        session['full_name'] = full_name
        flash('Profile updated successfully!', 'success')
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
