from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from werkzeug.utils import secure_filename
import os
from itsdangerous import URLSafeTimedSerializer
import mysql.connector


db_config = {
  'user': 'root',
  'password': 'root',
  'host': 'localhost',
  'port': 3306,
  'database': 'bank',
  'raise_on_warnings': True,
}
link = mysql.connector.connect(**db_config)

app = Flask(__name__)
app.secret_key = '123456'


@app.route('/')
def home():
    logged_in = 'email' in session
    return render_template('index.html', logged_in=logged_in, email=session.get('email'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            v = validate_email(email)  # validate and get info
            email = v["email"]  # replace with normalized form
        except EmailNotValidError as e:
            flash('Invalid email address!')
            return render_template('register.html'), 400
        if not password:
            flash('Password is required!')
            return render_template('register.html'), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            if result:
                flash('Email already exists!')
                return render_template('register.html'), 400
            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users (email, Password) VALUES (%s, %s)", (email, hashed_password))  # 注意列名的大小写
            connection.commit()
        except mysql.connector.Error as err:
            flash('An error occurred during registration. Please try again.')
            print("Something went wrong: {}".format(err))
            return render_template('register.html'), 500
        finally:
            cursor.close()
            connection.close()
        session['email'] = email
        session['logged_in'] = True
        flash('Registration successful!')
        return redirect(url_for('home'))
    return render_template('register.html')

def get_db_cursor():
    db = mysql.connector.connect(**db_config)
    return db.cursor()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password are required!')
            return render_template('login.html'), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            if not result:
                flash('Email not found!')
                return render_template('login.html'), 404
            
            hashed_password = result[1]  # 假设密码在第二列
            if check_password_hash(hashed_password, password):
                session['email'] = email
                session['logged_in'] = True
                return redirect(url_for('home'))
            else:
                flash('Incorrect password!')
                return render_template('login.html'), 401
        except mysql.connector.Error as err:
            flash('An error occurred. Please try again.')
            print("Something went wrong: {}".format(err))
        finally:
            cursor.close()
            connection.close()
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功注销。', 'success')
    return redirect(url_for('home'))


@app.route('/profile')
def profile():
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    # 此处应检索用户数据，如个人资料信息和头像等
    # user = get_user_profile(email)  # 示例函数，您需要根据实际情况实现
    # return render_template('profile.html', user=user)
    return render_template('profile.html', email=email)  # 暂时使用邮箱作为示例
    


def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='bank'
    )

@app.route('/comments')
def comments():
    if 'logged_in' not in session:
        flash('You need to be logged in to view comments.')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM abstracts")
        abstracts_data = cursor.fetchall()
        cursor.execute("SELECT * FROM introductory_materials")
        intro_data = cursor.fetchall()
    except mysql.connector.Error as err:
        flash('An error occurred while fetching comments: {}'.format(err))
        abstracts_data, intro_data = [], []
    finally:
        cursor.close()
        connection.close()

    return render_template('comments.html', abstracts=abstracts_data, intro=intro_data)

@app.route('/submit_comments', methods=['POST'])
def submit_comments():
    if 'logged_in' not in session:
        flash('You need to be logged in to submit comments.')
        return redirect(url_for('login'))
    
    email = session['email']
    abstracts_ids = request.form.getlist('abstracts_ids')
    intros_ids = request.form.getlist('intros_ids')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        for abstract_id in abstracts_ids:
            cursor.execute(
                "INSERT INTO submitted_comments (email, abstracts_and_executive_summaries) SELECT %s, content FROM abstracts WHERE id = %s",
                (email, abstract_id)
            )
        
        for intro_id in intros_ids:
            cursor.execute(
                "INSERT INTO submitted_comments (email, introductory_material) SELECT %s, content FROM introductory_materials WHERE id = %s",
                (email, intro_id)
            )
        
        connection.commit()
        flash('Comments submitted successfully.')
    except mysql.connector.Error as err:
        flash('An error occurred while submitting your comments: {}'.format(err))
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('home'))


@app.route('/view_comments')
def view_comments():
    if 'logged_in' not in session:
        flash('You need to be logged in to view this page.')
        return redirect(url_for('login'))
    
    email = session.get('email')  # 获取当前登录的用户邮箱
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM submitted_comments WHERE email = %s", (email,))
        comments_data = cursor.fetchall()
    except mysql.connector.Error as err:
        flash('An error occurred while fetching the comments: {}'.format(err))
        comments_data = []
    finally:
        cursor.close()
        connection.close()

    return render_template('view_comments.html', comments=comments_data)






@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/greet')
def greet():
    name = request.args.get('name', 'Guest')
    greeting = f'Hello, {name}!'
    return render_template('greet.html', greeting=greeting)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        feedback = request.form['feedback']
        return redirect(url_for('feedbackresult', feedback=feedback))
    return render_template('feedback.html')

@app.route('/feedbackresult/<feedback>')
def feedbackresult(feedback):
    return render_template('feedbackresult.html', feedback=feedback)

@app.route('/message')
def message():
    message = "Have a great day!"
    return render_template('message.html', message=message)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/current-time')
def current_time():
    now = datetime.datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return render_template('current_time.html', time=formatted_time)

@app.route('/api')
def api():
    return jsonify({"message": "Welcome to our API"})

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/gallery')
def gallery():
    images = ['image1.jpg', 'image2.jpg', 'image3.jpg']
    return render_template('gallery.html', images=images)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email')
    return render_template('confirmation.html', name=name, email=email)

if __name__ == '__main__':
    app.run(debug=True)
