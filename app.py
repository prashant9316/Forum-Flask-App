from flask import Flask, render_template, g, request, session, redirect, url_for
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = b'e\x153"\xc0Sx\xd8\x17X\x92U\xe1\xf2\x15\xe7\xf8\xb9|\xd5\xe4\x12\x17\xfb'


def current_user():
    user_result = None
    if 'user' in session:
        user = session['user']

        db = get_db()
        db.execute(
            'select id, name, password, expert, admin from users where name = %s', (user, ))
        user_result = db.fetchone()
    return user_result


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn.close()

    if hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur.close()


@app.route('/')
def index():
    user = current_user()

    db = get_db()
    db.execute(
        '''select questions.id, questions.questions, asker.name as asker_name, expert.name as expert_name
            from questions
            join users as asker on asker.id = questions.asked_by_id
            join users as expert on expert.id = questions.expert_id
            where questions.answer is not null''')
    questions = db.fetchall()

    return render_template('home.html', user=user, questions=questions)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = current_user()
    if request.method == 'POST':

        db = get_db()
        db.execute(
            'select id from users where name =%s', (request.form['name'], ))
        existing_user = db.fetchone()

        if existing_user:
            return render_template('register.html', user=user, error='User already exists')

        hashed_password = generate_password_hash(
            request.form['password'], method='sha256')
        db.execute('insert into users (name, password, expert, admin) values (%s, %s, %s, %s)', (
                   request.form['name'], hashed_password, '0', '0'))

        return redirect(url_for('login'))

    return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = current_user()
    if request.method == 'POST':
        db = get_db()

        name = request.form['name']
        password = request.form['password']

        db.execute(
            'select id, name, password from users where name = %s', (name, ))
        user_result = db.fetchone()

        if user_result:

            if check_password_hash(user_result['password'], password):
                session['user'] = user_result['name']
                return redirect(url_for('index'))
            else:
                return render_template('login.html', user=user, error='Oops! Bad Credentials')
        else:
            return render_template('login.html', user=user, error='Oops! Bad Credentials')

    return render_template('login.html', user=user)


@app.route('/question/<question_id>')
def question(question_id):
    user = current_user()
    db = get_db()
    db.execute(
        '''select questions.id, questions.answer, questions.questions, asker.name as asker_name, expert.name as expert_name
            from questions
            join users as asker on asker.id = questions.asked_by_id
            join users as expert on expert.id = questions.expert_id
            where questions.id = %s''', (question_id, ))
    question = db.fetchone()
    return render_template('question.html', user=user, question=question)


@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    user = current_user()
    db = get_db()
    if user['expert'] == 0:
        return redirect(url_for('index'))
    if request.method == 'POST':
        answer = request.form['answer']

        db.execute('update questions set answer = %s where id = %s', (
                   answer, question_id))


        return redirect(url_for('unanswered'))

    question_cur = db.execute(
        'select id, questions from questions where id = %s', (question_id, ))
    question = db.fetchone()

    return render_template('answer.html', user=user, question=question, id=id)


@app.route('/ask', methods=['GET', 'POST'])
def ask():
    user = current_user()
    if not user:
        return redirect(url_for('login'))

    if user['expert'] == 1:
        return redirect(url_for('index'))
    db = get_db()

    if request.method == 'POST':
        expert_id = request.form['expert']
        question = request.form['question']
        db.execute('insert into questions (questions, asked_by_id, expert_id) values (%s,%s,%s)', (
                   question, user['id'], expert_id))
        return redirect(url_for('index'))

    db.execute('select id, name from users where expert = True')
    experts_result = db.fetchall()

    return render_template('ask.html', user=user, experts=experts_result)


@app.route('/unanswered')
def unanswered():
    user = current_user()
    if not user:
        return redirect(url_for('login'))

    if user['expert'] == 0:
        return redirect(url_for('index'))
    db = get_db()
    questions_cur = db.execute(
        '''select questions.id, questions.questions, users.name
            from questions
            join users on users.id = questions.asked_by_id
            where questions.answer is null and expert_id = %s''', (user['id'], ))
    questions = db.fetchall()

    return render_template('unanswered.html', user=user, questions=questions)


@app.route('/users')
def users():
    user = current_user()

    if not user:
        return redirect(url_for('login'))

    if user['admin'] == 0:
        return redirect(url_for('index'))

    db = get_db()
    db.execute('select id, name, admin, expert from users')
    users_result = db.fetchall()

    return render_template('users.html', user=user, users=users_result)


@app.route('/user_settings')
def user_settings():
    user = current_user()

    if not user:
        return redirect(url_for('login'))

    if user['admin'] == 0:
        return redirect(url_for('index'))

    db = get_db()
    db.execute('select id, name, admin, expert from users')
    users_result = db.fetchall()
    return render_template('user_settings.html', user=user, users=users_result)


@app.route('/user_settings/admin_settings/<user_id>', methods=['GET', 'POST'])
def admin_settings(user_id):
    user = current_user()
    message = None
    if not user:
        return redirect(url_for('login'))
    if user['admin'] == 0:
        return redirect(url_for('index'))
    db = get_db()
    if request.method == 'POST':
        if (request.form['password'] != request.form['password_check']):
            message = 'ERROR: Entered passwords doesn\'t match!!!!!!'
        else:
            hashed_password = generate_password_hash(
                request.form['password'], method='sha256')
            db.execute('update users set password = %s where id = %s',
                       (hashed_password, user_id))

            message = 'Account password changed!!'

    users_cur = db.execute(
        'select id, name, expert from users where id = %s', (user_id, ))
    users_details = db.fetchone()
    return render_template('admin_settings.html', user=user, users_details=users_details, message=message)


@app.route('/reset_pass/<user_name>', methods=['GET', 'POST'])
def reset_pass(user_name):
    user = current_user()
    message = None
    if not user:
        return redirect(url_for('login'))

    db = get_db()
    if request.method == 'POST':
        if (request.form['password'] != request.form['password_check']):
            message = 'ERROR: Entered passwords doesn\'t match!!!!!!'
        else:
            hashed_password = generate_password_hash(
                request.form['password'], method='sha256')
            db.execute('update users set password = %s where name = %s',
                       (hashed_password, user_name))

            message = 'Account password changed!!'

    return render_template('reset_pass.html', user=user, message=message)


@app.route('/deleteuser/<user_id>')
def deleteuser(user_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    if user['admin'] == 1:
        return redirect(url_for('index'))

@app.route('/promote/<user_id>')
def promote(user_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    if user['admin'] == 0:
        return redirect(url_for('index'))
    db = get_db()
    db.execute('update users set expert = True where id = %s', (user_id, ))
    return redirect(url_for('users'))


@app.route('/demote/<user_id>')
def demote(user_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    if user['admin'] == 0:
        return redirect(url_for('index'))
    db = get_db()
    db.execute('update users set expert = False where id = %s', (user_id, ))
    return redirect(url_for('users'))


@app.route('/logout')
def logout():
    user = current_user()

    session.pop('user', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
