
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
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
import re

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@34.75.150.200/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.75.150.200/proj1part2"
#
DATABASEURI = "postgresql://tn2415:7841@34.75.150.200/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


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


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT * FROM Users")
  names = []
  for result in cursor:
    names.append(result['username'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #
  #     # creates a <div> tag for each element in data
  #     # will print:
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
#
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/register')
def register():
  return render_template("register.html")

@app.route('/login')
def login():
  return render_template("login.html")

@app.route('/search')
def search():
  return render_template("search.html")

# Example of adding new data to the database
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
  return redirect('/search')

@app.route('/olduser', methods=['POST'])
def olduser():
  username = request.form['name']
  password = request.form['password']
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
  return render_template("search.html")

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

@app.route('/searchtopic')
def searchtopic():
  topic = request.args.get('topic')
  cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q, Is_Categorized_As i WHERE i.qid = q.qid AND i.topic_name = %s", topic)
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  if len(questions) == 0:
    message = "no questions related to this topic yet"
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = questions)
  return render_template("search.html", **context)

@app.route('/searchcompany')
def searchcompany():
  company = request.args.get('company')
  cursor = g.conn.execute("SELECT q.qid, a.last_time_asked, q.title, q.content FROM Questions q, Asked_By a WHERE a.qid = q.qid AND a.company_name = %s", company)
  questions = []
  for result in cursor:
    questions.append(result)
  cursor.close()
  if len(questions) == 0:
    message = "no questions related to this company yet"
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

@app.route('/searchdiscussion')
def searchdiscussion():
  qid = request.args.get('discussion')
  cursor = g.conn.execute("SELECT d.content, d.posted_at, d.username FROM Discussions_Belong_To d WHERE d.post_id = %s", qid)
  discussion = []
  for result in cursor:
    discussion.append(result)
  cursor.close()
  if len(discussion) == 0:
    message = "no disscusion on this question yet"
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = discussion)
  return render_template("search.html", **context)

@app.route('/searchtrained')
def searchtrained():
  username = request.args.get('trained')

  cursor = g.conn.execute("SELECT * FROM Users u WHERE u.username = %s", username)
  record = cursor.fetchone()
  if record is None:
    message = "Username does not exist."
    context = dict(msg = message)
    return render_template("search.html", **context)

  cursor = g.conn.execute("SELECT q.qid, q.title, q.content, u.trained_at FROM Questions q, User_Trained_Question u WHERE q.qid = u.qid AND u.username = %s", username)
  discussion = []
  for result in cursor:
    discussion.append(result)
  cursor.close()
  if len(discussion) == 0:
    message = "You have not trained on any question yet."
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = discussion)
  return render_template("search.html", **context)

@app.route('/searchliked')
def searchliked():
  username = request.args.get('liked')

  cursor = g.conn.execute("SELECT * FROM Users u WHERE u.username = %s", username)
  record = cursor.fetchone()
  if record is None:
    message = "Username does not exist."
    context = dict(msg = message)
    return render_template("search.html", **context)

  cursor = g.conn.execute("SELECT q.qid, q.title, q.content FROM Questions q, User_Liked_Question u WHERE q.qid = u.qid AND u.username = %s", username)
  discussion = []
  for result in cursor:
    discussion.append(result)
  cursor.close()
  if len(discussion) == 0:
    message = "You have not liked any question yet."
    context = dict(msg = message)
    return render_template("search.html", **context)
  context = dict(data = discussion)
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
