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
    'password': '',
    'host': 'localhost',
    'port': '8889',
    'database': 'Bank'  # Replace with your actual database name
}

db = mysql.connector.connect(**db_config)

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
            # email is not valid, handle exception
            return str(e), 400
        if not password:
            return 'Password is required!', 400
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
        if result:
            return 'Email already exists!'
        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (email, password, profile_picture) VALUES (%s, %s, %s)", (email, hashed_password, 'default.jpg'))        
        db.commit()
        return 'Registration successful!'
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password are required!')
            return render_template('login.html'), 400
        
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()  # It's good practice to close the cursor when you're done with it

        if not result:
            flash('Email not found!')
            return render_template('login.html'), 404
        
        hashed_password = result[2]  # Assuming the password is at index 2
        if check_password_hash(hashed_password, password):
            session['email'] = email
            session['logged_in'] = True  # This line marks the user as logged in
            return redirect(url_for('home'))  # Redirect to the home page after successful login
        else:
            flash('Incorrect password!')
            return render_template('login.html'), 401
    
    # This is outside the 'POST' check, so it handles 'GET' requests
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
        password='12345',
        database='Bank'
    )

@app.route('/comments')
def comments():
    if 'logged_in' not in session:
        flash('You need to be logged in to view comments.')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM comments_template")
    comment_list = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('comments.html', comments=comment_list)

@app.route('/submit_comments', methods=['POST'])
def submit_comments():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # 获取选中的评论ID列表
    selected_comment_ids = request.form.getlist('comments')
    # 这里可以添加逻辑来处理选中的评论
    # 例如，保存选中的评论ID到数据库

    # 提示用户提交成功，并渲染确认页面
    flash('Comments submitted successfully!')
    return render_template('submit_comments.html')





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
