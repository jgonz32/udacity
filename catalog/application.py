from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask import session as login_session
from functools import wraps
import random, string

import catalog_queries

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from db.catalog_database_setup import Base, Manufacturer, Model, Specifications, CatalogUser
from flask.ext.seasurf import SeaSurf

app = Flask(__name__)

#passing app to SeaSurf to protect post requests against CSRF attacks
csrf = SeaSurf(app)

queries = catalog_queries.CatalogQueries('postgresql+psycopg2://catalog:b#stCatal0g@/phonecatalog')

CLIENT_ID = json.loads(
  open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Smart Phones Catalog Application"

@app.route('/login')
def showLogin():

  state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
  login_session['state'] = state

  recent_models_added_list = queries.get_recent_models_list()
  
  return render_template("login.html", manufacturers=queries.get_phone_models_count(), recent_models=recent_models_added_list, STATE=state)

#login required function to use as decoreator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')    
        return f(*args, **kwargs)
    return decorated_function    

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
  # Only disconnect a connected user.
  credentials = login_session.get('credentials')
  if credentials is None:
    response = make_response(json.dumps('Current user not connected.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response 
  print credentials
  access_token = credentials
  url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
  h = httplib2.Http()
  result = h.request(url, 'GET')[0]
  if result['status'] != '200':
    # For whatever reason, the given token was invalid.
    response = make_response(json.dumps('Failed to revoke token for given user.', 400))
    response.headers['Content-Type'] = 'application/json'
    return response


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
  if 'provider' in login_session:
    if login_session['provider'] == 'google':
      gdisconnect()
      del login_session['gplus_id']
      del login_session['credentials']

    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['provider']
    flash("You have been signed out successfully!")
    return redirect(url_for('showCatalog'))
  else:
    flash("You were not logged in")
    return redirect(url_for('showCatalog'))

@csrf.exempt
@app.route('/gconnect', methods=['POST'])
def gconnect():
# Validate state token 
  if request.args.get('state') != login_session['state']:
    response = make_response(json.dumps('Invalid state parameter.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  # Obtain authorization code
  code = request.data
  
  try:
    # Upgrade the authorization code into a credentials object
    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(code)
  except FlowExchangeError:
    response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  
  # Check that the access token is valid.
  access_token = credentials.access_token
  url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
         % access_token)
  h = httplib2.Http()
  result = json.loads(h.request(url, 'GET')[1])
  # If there was an error in the access token info, abort.
  if result.get('error') is not None:
    response = make_response(json.dumps(result.get('error')), 500)
    response.headers['Content-Type'] = 'application/json'

    
  # Verify that the access token is used for the intended user.
  gplus_id = credentials.id_token['sub']
  if result['user_id'] != gplus_id:
    response = make_response(
        json.dumps("Token's user ID doesn't match given user ID."), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Verify that the access token is valid for this app.
  if result['issued_to'] != CLIENT_ID:
    response = make_response(
        json.dumps("Token's client ID does not match app's."), 401)
    print "Token's client ID does not match app's."
    response.headers['Content-Type'] = 'application/json'
    return response

  stored_credentials = login_session.get('credentials')
  stored_gplus_id = login_session.get('gplus_id')
  if stored_credentials is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('Current user is already connected.'),
                             200)
    response.headers['Content-Type'] = 'application/json'
    return response
    
  # Store the access token in the queries.session for later use.
  login_session['credentials'] = credentials.access_token
  login_session['gplus_id'] = gplus_id
 
  
  # Get user info
  userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
  params = {'access_token': credentials.access_token, 'alt':'json'}
  answer = requests.get(userinfo_url, params=params)
  
  data = answer.json()

  login_session['username'] = data['name']
  login_session['picture'] = data['picture']
  login_session['email'] = data['email']
 
  login_session['provider'] = 'google'
 # See if a user exists, if it doesn't make a new one
  user_id = queries.get_user_id(login_session['email'])  # getUserID(login_session['email'])
  if not user_id:
    user_id = queries.create_user(login_session)
  login_session['user_id'] = user_id
  
  return redirect(url_for('showCatalog'))
  
# show main page
@app.route('/')
@app.route('/catalog')
@app.route('/catalog/')
def showCatalog():
    
    manufacturers = queries.get_phone_models_count()
    recent_models = queries.get_recent_models_list()
    
    if 'username' not in login_session:
        return render_template("phonecatalog.html", manufacturers=manufacturers, recent_models=recent_models)
    else:
        return render_template("phonecatalog-signedin.html", manufacturers=manufacturers, recent_models=recent_models, username=login_session['username'])

# create a new phone model in the database
@app.route('/catalog/phones/add', methods=['GET', 'POST'])
@login_required
def newManufacturerPhone():
    
    if request.method == 'POST':
        
        manufacturer_selected = request.form['manufacturer_list']
        manufacturer = queries.search_by_manufacturer_name(manufacturer_selected)
        manufacturer_id = manufacturer.id
        new_phone_model = Model(name=request.form['name'], user_id=login_session['user_id'], manufacturer_id=manufacturer_id)
        queries.session.add(new_phone_model)
        queries.session.commit()
        
        model = queries.search_by_phone_model_id(new_phone_model.id)
        
        # get specs submitted in form
        size = request.form['size']
        weight = request.form['weight']
        camera = request.form['camera']
        os = request.form['os']
        memory = request.form['memory']
        display = request.form['display']
        
        specs = Specifications(size=size, weight=weight, camera=camera, os=os, memory=memory, display=display, model_id=model.id)
        
        queries.session.add(specs)
        queries.session.commit()
        
        flash('New Smartphone model %s Successfully Created' % new_phone_model.name)
        
        return redirect(url_for('showCatalog'))
    else:
        return render_template("newPhoneModel.html", manufacturers=queries.get_phone_models_count(), recent_models=queries.get_recent_models_list(), username=login_session['username'])
        
# edit selected phone model
@app.route('/catalog/<int:manufacturer_id>/<int:model_id>/edit', methods=['GET', 'POST'])
@login_required
def editManufacturerPhone(manufacturer_id, model_id):
 
    edited_phone_model = queries.search_by_phone_model_id(model_id)

    if edited_phone_model.user_id != login_session['user_id']:
        return "Not authorized"

    if request.method == 'POST':

        edited_phone_model.name = request.form['phoneModel']
        queries.session.add(edited_phone_model)
        queries.session.commit()

        specs = queries.search_specifications_by_model_id(edited_phone_model.id)
        
        # Update specs from form
        specs.size = request.form['size']
        specs.weight = request.form['weight']
        specs.camera = request.form['camera']
        specs.os = request.form['os']
        specs.memory = request.form['memory']
        specs.display = request.form['display']
        
        queries.session.add(specs)
        queries.session.commit()
        
        flash('%s Changes were Successfully Saved' % edited_phone_model.name)
        
        return redirect(url_for('showCatalog'))
    
    else:
        manufacturer = queries.search_by_manufacturer_id(manufacturer_id)
        phone_model = queries.search_by_phone_model_id(model_id)
        specs = queries.search_specifications_by_model_id(phone_model.id)
    
        return render_template("editPhoneModel.html", manufacturers=queries.get_phone_models_count(), recent_models=queries.get_recent_models_list(), specs=specs, username=login_session['username'], model=phone_model, manufacturer=manufacturer)

# delete selected phone model    
@app.route('/catalog/<int:manufacturer_id>/<int:model_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteManufacturerPhone(manufacturer_id, model_id):

    deleted_phone_model = queries.search_by_phone_model_id(model_id)

    if deleted_phone_model.user_id != login_session['user_id']:
        return "Not authorized"

    if request.method == 'POST':

        specs = queries.search_specifications_by_model_id(deleted_phone_model.id)
        queries.session.delete(specs)
        queries.session.delete(deleted_phone_model)
        queries.session.commit()
        
        flash('Phone %s has been successfully deleted' % deleted_phone_model.name)
        
        return redirect(url_for('showCatalog'))

    else:
        return render_template("newPhoneModel.html", manufacturers=queries.get_phone_models_count(), recent_models=queries.get_recent_models_list())

# Shows phone model specification
@app.route('/catalog/<int:manufacturer_id>/<int:model_id>/specs')
def showPhoneSpecs(manufacturer_id, model_id):

    specifications = queries.session.query(Model, Specifications).join(Specifications, Specifications.model_id == Model.id).filter(Model.id == model_id).one()[1]
    phone_model = queries.search_by_phone_model_id(model_id)
    manufacturer = queries.search_by_manufacturer_id(manufacturer_id)
    
    if 'username' not in login_session:
        return render_template("phonespecs.html", manufacturers=queries.get_phone_models_count(), recent_models=queries.get_recent_models_list(), manufacturer=manufacturer.name,model=phone_model.name, specs=specifications)
    else:
        if phone_model.user_id == login_session['user_id']:
            return render_template("phonespecs-signedin.html", manufacturers=queries.get_phone_models_count(), recent_models=queries.get_recent_models_list(), manufacturer=manufacturer, model=phone_model, specs=specifications, username=login_session['username'], authorized=True)
        else:
            flash('You are not authorized to make changes or delete this phone model.')
            return render_template("phonespecs-signedin.html", manufacturers=queries.get_phone_models_count(), recent_models=queries.get_recent_models_list(), manufacturer=manufacturer, model=phone_model, specs=specifications, username=login_session['username'], authorized=False)
 

# JSON APIs to view a list of all manufacturer in the catalog
@app.route('/catalog/manufacturer/phones/JSON')
def manufacturerPhonesJSON():
    models = queries.get_all_phone_models()  # queries.session.query(Model).all()    
    return jsonify(Model=[m.serialize for m in models])

# JSON APIs to view a list of all manufacturer and their phones in the catalog
@app.route('/catalog/manufacturer/JSON')
def manufacturerJSON():
    manufacturers = queries.get_all_manufacturers() 
    return jsonify(manufacturers=[r.serialize for r in manufacturers])

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
