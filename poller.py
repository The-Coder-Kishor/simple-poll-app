from flask import Flask, request, render_template, flash, redirect
import json
import os  
import sqlite3

from flaskwebgui import FlaskUI

db_path = './polls.db'
if not os.path.exists(db_path):
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS polls
                (id INTEGER PRIMARY KEY, title TEXT, active INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS votes
                (id INTEGER PRIMARY KEY, poll_id INTEGER, voter_name TEXT, voter_class TEXT, voter_roll TEXT, votes INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_auth
                (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''INSERT INTO admin_auth (username, password) VALUES (?, ?)''', ('admin', 'admin'))
    conn.commit()
    conn.close()


app = Flask(__name__)

@app.route('/')
def home():
    # find number of active polls
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''SELECT COUNT(*) FROM polls WHERE active = 1''')
    active_polls = c.fetchone()[0]
    
    if active_polls == 0:
        conn.close()
        return render_template('./home.html', active_polls = active_polls, message = 'No active polls')
    else:
        #get poll id and poll title
        c.execute('''SELECT id, title FROM polls WHERE active = 1''')
        answer = c.fetchone()
        poll_id = answer[0]
        poll_title = answer[1]  
        c.execute('''SELECT * FROM votes WHERE poll_id = ?''', (poll_id,))
        users = c.fetchall()
        conn.close()
        candidates = []
        for user in users:
            candidate = {
                'id': user[0],
                'name': user[2],
                'rollNumber': user[4],
                'class': user[3],
            }
            candidates.append(candidate)
        return render_template('./index.html', pollid = poll_id, polltitle = poll_title, candidates=candidates)

@app.route('/create_poll')
def create_poll():
    #find number of active polls
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''SELECT COUNT(*) FROM polls WHERE active = 1''')
    active_polls = c.fetchone()[0]
    conn.close()
    if active_polls > 0:
        return render_template('./already_poll.html')
    else:
        return render_template('./create_poll.html')

@app.route('/add_poll', methods=['POST'])
def add_poll():
    data = json.loads(request.data)
    pollTitle = data['pollTitle']
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''INSERT INTO polls (title, active) VALUES (?, 1)''', (pollTitle,))
    ## how to get the index of the last inserted row of poll table
    c.execute('''SELECT id FROM polls ORDER BY id DESC LIMIT 1''')
    poll_id = c.fetchone()[0]
    for candidate in data['people']:
        name = candidate['name']
        rollNumber = candidate['rollNumber']
        cls = candidate['class']
        c.execute('''INSERT INTO votes (poll_id, voter_name, voter_class, voter_roll, votes) VALUES (?, ?, ?, ?, 0)''', (poll_id, name, cls, rollNumber))
    conn.commit()
    conn.close()
    return {'status': 'success'}

@app.route('/end_poll', methods=['POST'])
def end_poll():
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''SELECT id FROM polls WHERE active = 1''')
    poll_id = c.fetchone()[0]
    if(poll_id):
        c.execute('''UPDATE polls SET active = 0 WHERE id = ?''', (poll_id,))
    conn.commit()
    conn.close()
    return {'status': 'success'}

@app.route('/vote', methods=['POST'])
def add_vote():
    data = json.loads(request.data)
    candidate_id = data['candidateId']
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''SELECT votes FROM votes WHERE id = ?''', (candidate_id,))
    votes = c.fetchone()[0]
    votes += 1
    c.execute('''UPDATE votes SET votes = ? WHERE id = ?''', (votes, candidate_id))
    conn.commit()
    conn.close()
    return {'status': 'success'}

@app.route('/redirect', methods=['POST'])
def redirect_to_page():
    data = json.loads(request.data)
    password = data['password']
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''SELECT password FROM admin_auth WHERE username = ?''', ('admin',))
    correct_password = c.fetchone()[0]
    conn.close()
    if password == correct_password:
        return {'status': data['endpoint']}
    else:
        return {'status': 'failure'}
    
@app.route('/view_polls')
def show_polls():
    #get all polls
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM polls''')
    polls = c.fetchall()
    #for each poll get all candidate results
    poll_results = []
    for poll in polls:
        poll_id = poll[0]
        poll_title = poll[1]
        c.execute('''SELECT * FROM votes WHERE poll_id = ?''', (poll_id,))
        users = c.fetchall()
        candidates = []
        for user in users:
            candidate = {
                'id': user[0],
                'name': user[2],
                'rollNumber': user[4],
                'class': user[3],
                'votes': user[5]
            }
            candidates.append(candidate)
        status = poll[2] == 1
        poll_result = {
            'poll_id': poll_id,
            'poll_title': poll_title,
            'active': status,
            'candidates': candidates
        }
        poll_results.append(poll_result)
    conn.close()
    print(poll_results)
    return render_template('./polls.html', poll_results=poll_results)

@app.route('/change_password')
def change_password():
    #get current passowrd
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''SELECT password FROM admin_auth WHERE username = ?''', ('admin',))
    password = c.fetchone()[0]
    conn.close()
    return render_template('./change_password.html', curr = password)

@app.route('/update_password', methods=['POST'])
def update_password():
    data = json.loads(request.data)
    new_password = data['newValue']
    conn = sqlite3.connect('./polls.db')
    c = conn.cursor()
    c.execute('''UPDATE admin_auth SET password = ? WHERE username = ?''', (new_password, 'admin'))
    conn.commit()
    return {'status': 'success'}


if __name__ == '__main__':
    FlaskUI(app=app, server="flask", width=800, height=600).run()