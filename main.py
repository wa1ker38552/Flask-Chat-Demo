from flask import render_template
from flask import make_response
from flask import redirect
from flask import request
from flask import Flask
from replit import db


app = Flask(__name__)

@app.route('/')
def home():
  if request.cookies.get('token') is None:
    return redirect('/login', code=302)
  else:
    data = {}
    data['chats'] = db['chat_data']
    if not request.cookies.get('selected') is None:
      try:
        data['messages'] = db['chat_data'][request.cookies.get('selected')]['messages']
      except KeyError:
        # chat was deleted while selected by another user
        response = make_response(redirect('/', code=302))
        response.set_cookie('selected', '', expires=0)

        return response
    else:
      data['messages'] = []
    data['profile'] = db['account_data']
    return render_template('index.html', data=data)

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'GET':
    if request.args.get('success') == 'false':
      return render_template('login.html', data=request.args.get('reason'))
    return render_template('login.html', data=None)
  else:
    # post request
    username = request.form['username']
    password = request.form['password']

    if username in db['account_data']:
      if password == db['account_data'][username]['password']:
        response = make_response(redirect('/', code=302))
        response.set_cookie('token', str(hash(username+password)))
        response.set_cookie('username', username)

        return response
      else:
        return redirect('/login?success=false&reason=Incorrect password', code=302)
    else:
      return redirect('/login?success=false&reason=Account does not exist', code=302)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
  if request.method == 'GET':
    if request.args.get('success') == 'false':
      return render_template('signup.html', data=request.args.get('reason'))
    return render_template('signup.html', data=None)
  else:
    # post request
    username = request.form['username']
    password = request.form['password']

    if not username in db['account_data']:
      if username != '' and password != '':
        db['account_data'][username] = {
          'password': password,
          # default profile
          'profile': 'https://www.citypng.com/public/uploads/preview/black-user-member-guest-icon-31634946589seopngzc1t.png'
        }
        
        response = make_response(redirect('/', code=302))
        response.set_cookie('token', str(hash(username+password)))
        response.set_cookie('username', username)

        return response
      else:
        return redirect('/signup?success=false&reason=Invalid character', code=302)
    else:
      return redirect('/signup?success=false&reason=Account already exists', code=302)

@app.route('/logout')
def logout():
  response = make_response(redirect('/', code=302))
  response.set_cookie('token', '', expires=0)
  response.set_cookie('username', '', expires=0)
  
  return response

@app.route('/create', methods=['POST', 'GET'])
def createchat():
  if request.method == 'GET':
    return render_template('createchat.html')
  else:
    # post request
    if not request.form['name'] == '':
      if not request.form['name'] in db['chat_data']:
        if not len(request.form['name']) > 20:
          db['chat_data'][request.form['name']] = {
            'owner': request.cookies.get('username'),
            'messages': []
          }
        
        return redirect('/', code=302)
    return redirect('/create', code=302)

@app.route('/api/delete')
def deletechat():
  if request.cookies.get('username') == db['chat_data'][request.cookies.get('selected')]['owner']:
    del db['chat_data'][request.cookies.get('selected')]

    response = make_response(redirect('/', code=302))
    response.set_cookie('selected', '', expires=0)

    return response
  else:
    return redirect('/?success=false', code=302)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
  if request.method == 'GET':
    return render_template('settings.html')
  else:
    if request.form['url'] != None:
      db['account_data'][request.cookies.get('username')]['profile'] = request.form['url']
    return redirect('/settings?success=true', code=302)

@app.route('/api/select')
def select():
  response = make_response(redirect('/', code=302))
  response.set_cookie('selected', request.args.get('chat'))

  return response

@app.route('/api/message', methods=['POST'])
def message():
  db['chat_data'][request.cookies.get('selected')]['messages'].append(
    {'author': request.cookies.get('username'), 'message': request.form['message']}
  )
  return ('', 204)

@app.route('/api/messagehistory')
def messagehistory():
  # endpoint for fetching message history
  try:
    return [dict(i) for i in db['chat_data'][request.cookies.get('selected')]['messages']]
  except KeyError:
    return []

@app.route('/api/profile')
def profile():
  # endpoint for fetching user profile
  user = request.args.get('user')
  if user in db['account_data']:
    return db['account_data'][user]['profile']
  else:
    return {'success': False}

    
# db['account_data'] = {}
# db['chat_data'] = {}
app.run(host='0.0.0.0', port=8080)
