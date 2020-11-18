
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, make_response
import re
from datetime import date
from datetime import datetime

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DATABASEURI = "postgresql://tn2415:7841@34.75.150.200/proj1part2"
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  resp = make_response(render_template("index.html"))
  resp.set_cookie('username', '', expires=0)
  return resp

@app.route('/register')
def register():
  return render_template("register.html")

@app.route('/login')
def login():
  return render_template("login.html")

@app.route('/search')
def search():
  return render_template("search.html")

@app.route('/newuser', methods=['POST'])
def add():
  username = request.form['name']
  if not username or len(username) > 20:
    message = "invalid username length"
    context = dict(msg = message)
    return render_template("register.html", **context)

  password = request.form['password']
  if not password or len(password) > 20:
    message = "invalid password length"
    context = dict(msg = message)
    return render_template("register.html", **context)

  cursor = g.conn.execute("SELECT * FROM Users u WHERE u.username = %s", username)
  record = cursor.fetchone()
  if record is not None:
    message = "username already exists"
    context = dict(msg = message)
    return render_template("register.html", **context)

  email = request.form['email']
  if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
    message = "email invalid"
    context = dict(msg = message)
    return render_template("register.html", **context)

  firstname = request.form['firstname']
  lastname = request.form['lastname']
  g.conn.execute('INSERT INTO Users(username, password, email, first_name, last_name) VALUES (%s, %s, %s, %s, %s)', username, password, email, firstname, lastname)
  cursor.close()
  return redirect('/')

@app.route('/olduser')
def olduser():
  username = request.args.get('name')
  password = request.args.get('password')
  cursor = g.conn.execute("SELECT * FROM Users u WHERE u.username = %s", username)
  record = cursor.fetchone()
  if record is None:
    message = "username does not exist"
    context = dict(msg = message)
    return render_template("login.html", **context)

  if record["password"] != password:
    message = "username and password does not match"
    context = dict(msg = message)
    return render_template("login.html", **context)
  cursor.close()
  resp = make_response(render_template("search.html"))
  resp.set_cookie('username', username)
  return resp

@app.route('/question')
def question():
  qid = request.args.get('qid')
  cursor_q = g.conn.execute("SELECT q.title, q.content FROM Questions q WHERE q.qid = %s", qid)
  cursor_d = g.conn.execute("SELECT d.content, d.posted_at, d.username FROM Discussions_Belong_To d WHERE d.qid = %s", qid)
  question = cursor_q.fetchone()
  if question is None:
    message = "Problem " + qid + " does not exist."
    context = dict(msg = message)
    return render_template("question.html", **context)
  cursor_q.close()
  context = dict(question = question)
  comment = []
  for result in cursor_d:
    comment.append(result)
  cursor_d.close()
  context = dict(comment = comment, question = question)
  resp = make_response(render_template("question.html", **context))
  resp.set_cookie('qid', qid)
  return resp

@app.route('/updatelike', methods=['GET', 'POST'])
def updatelike():
  username = request.cookies.get('username')
  qid = request.cookies.get('qid')
  cursor_q = g.conn.execute("SELECT q.title, q.content FROM Questions q WHERE q.qid = %s", qid)
  cursor_d = g.conn.execute("SELECT d.content, d.posted_at, d.username FROM Discussions_Belong_To d WHERE d.qid = %s", qid)
  question = cursor_q.fetchone()
  cursor_q.close()
  comment = []
  for result in cursor_d:
    comment.append(result)
  cursor_d.close()
  cursor = g.conn.execute("SELECT * FROM User_Liked_Question u WHERE u.qid = %s AND u.username = %s", qid, username)
  record = cursor.fetchone()
  cursor.close()
  message = ""
  if record is not None:
    message = "You've already liked this question!"
  else:
    g.conn.execute('INSERT INTO User_Liked_Question(username, qid) VALUES (%s, %s)', username, qid)
    message = "You've successfully liked this question!"
  context = dict(comment = comment, question = question, status = message)
  return render_template("question.html", **context)

@app.route('/addcomment', methods=['POST'])
def addcomment():
  username = request.cookies.get('username')
  qid = request.cookies.get('qid')
  content = request.form['input']
  message = ""
  if not content:
    message = "Empty comment cannot be added."
  else:
    new_post_id = 1 + g.conn.execute("SELECT MAX(d.post_id) FROM Discussions_Belong_To d").fetchone()[0]
    g.conn.execute('INSERT INTO Discussions_Belong_To(post_id, content, posted_at, qid, username) VALUES (%s, %s, %s, %s, %s)', new_post_id, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), qid, username)
    message = "Comment successfully added!"

  cursor_q = g.conn.execute("SELECT q.title, q.content FROM Questions q WHERE q.qid = %s", qid)
  cursor_d = g.conn.execute("SELECT d.content, d.posted_at, d.username FROM Discussions_Belong_To d WHERE d.qid = %s", qid)
  question = cursor_q.fetchone()
  cursor_q.close()
  comment = []
  for result in cursor_d:
    comment.append(result)
  cursor_d.close()
  context = dict(comment = comment, question = question, inputStatus = message)
  return render_template("question.html", **context)

@app.route('/updatetrain', methods=['GET', 'POST'])
def updatetrain():
  username = request.cookies.get('username')
  qid = request.cookies.get('qid')
  cursor_q = g.conn.execute("SELECT q.title, q.content FROM Questions q WHERE q.qid = %s", qid)
  cursor_d = g.conn.execute("SELECT d.content, d.posted_at, d.username FROM Discussions_Belong_To d WHERE d.qid = %s", qid)
  question = cursor_q.fetchone()
  cursor_q.close()
  comment = []
  for result in cursor_d:
    comment.append(result)
  cursor_d.close()
  cursor = g.conn.execute("SELECT * FROM User_Trained_Question u WHERE u.qid = %s AND u.username = %s", qid, username)
  record = cursor.fetchone()
  cursor.close()
  message = ""
  if record is not None:
    message = "You worked on this question on " + record[2].strftime("%m/%d/%Y") + " already!"
  else:
    g.conn.execute('INSERT INTO User_Trained_Question(username, qid, trained_at) VALUES (%s, %s, %s)', username, qid, date.today())
    message = "You have succsefully trained on this problem, keep it up!"
  context = dict(comment = comment, question = question, status = message)
  return render_template("question.html", **context)

@app.route('/searchdifficulty')
def searchdifficulty():
  difficulty = request.args.get('difficulty')
  level = 1
  if difficulty == "medium":
    level = 2
  elif difficulty == "hard":
    level = 3
  cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q WHERE q.difficulty = %s", level)
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  context = dict(data = questions)
  return render_template("search.html", **context)

@app.route('/searchsource')
def searchsource():
  source = request.args.get('source')
  cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q WHERE q.source = %s", source)
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  if len(questions) == 0:
    message = "No question from " + source + " yet. Please try other sources."
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = questions)
  return render_template("search.html", **context)

@app.route('/searchtopic')
def searchtopic():
  topic = request.args.get('topic')
  cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q, Is_Categorized_As i WHERE i.qid = q.qid AND i.topic_name = %s ORDER BY q.qid", topic)
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  if len(questions) == 0:
    message = "No questions related to this topic yet"
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = questions)
  return render_template("search.html", **context)

@app.route('/searchmostliked')
def searchmostliked():
  number = request.args.get('number')
  cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q, User_Liked_Question u WHERE q.qid = u.qid GROUP BY q.qid HAVING COUNT(*) >= %s ORDER BY q.qid", number)
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  if len(questions) == 0:
    message = "No questions received this much likes. Please try other numbers."
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = questions)
  return render_template("search.html", **context)

@app.route('/searchcompany')
def searchcompany():
  company = request.args.get('company')
  cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q, Asked_By a WHERE a.qid = q.qid AND a.company_name = %s ORDER BY q.qid", company)
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  if len(questions) == 0:
    message = "No questions related to this company yet."
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = questions)
  return render_template("search.html", **context)

@app.route('/searchreal')
def searchreal():
  q_type = request.args.get('real')
  cursor = None
  if q_type == "all":
    cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q")
  else:
    cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q WHERE company_or_not = '1'")
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  context = dict(data = questions)
  return render_template("search.html", **context)

@app.route('/searchtrained')
def searchtrained():
  username = request.cookies.get('username')
  cursor = g.conn.execute("SELECT * FROM Users u WHERE u.username = %s", username)
  record = cursor.fetchone()
  if record is None:
    message = "Cannot identify user. Please login first."
    context = dict(msg = message)
    return render_template("search.html", **context)

  cursor = g.conn.execute("SELECT q.qid, q.title, q.content, u.trained_at FROM Questions q, User_Trained_Question u WHERE q.qid = u.qid AND u.username = %s ORDER BY q.qid", username)
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  if len(questions) == 0:
    message = "You have not trained on any question yet."
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = questions)
  return render_template("search.html", **context)

@app.route('/searchliked')
def searchliked():
  username = request.cookies.get('username')
  cursor = g.conn.execute("SELECT * FROM Users u WHERE u.username = %s", username)
  record = cursor.fetchone()
  if record is None:
    message = "Cannot identify user. Please login first."
    context = dict(msg = message)
    return render_template("search.html", **context)
  cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q, User_Liked_Question u WHERE q.qid = u.qid AND u.username = %s ORDER BY q.qid", username)
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  if len(questions) == 0:
    message = "You have not liked any question yet."
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = questions)
  return render_template("search.html", **context)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
