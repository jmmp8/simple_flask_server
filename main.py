# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_app]
from flask import Flask, redirect, url_for, request, render_template
import json
from firebase_config import config
import pyrebase
import sys

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

fb = pyrebase.initialize_app(config)
db = fb.database()


def filters(food):
    return (''.join(c for c in food if c not in ' _-/\\')).lower()

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Hello World!'

@app.route('/foodlist')
def food_list():
   try:
       foods = list(db.child("Recipes").get().val().keys())

       return json.dumps(foods)
   except Exception as e:
       return "failed to get food list: %s" % e


@app.route('/freefood/<date>')
def free_food(date):
    """
    event (string)
    start/end HH:MM
    location address
    org/details (string)
    data of format (string) YYYY-MM-DD
    """

    try:
        free = db.child('Freefood').get().val()

        def event(event, start, end, org, location, details = "None", date=date):
            return locals()

        free = [event(k, free[k]['start'], free[k]['end'], 
                      free[k]['organization'], free[k]['location'],
                      free[k]['details']) for k in free if free[k]['date'] == date]
        free.sort(key = lambda a: a['start'])

        return json.dumps(free)
    except Exception as e:
        return "Failed to get free food list %s" % e

@app.route('/success')
def yes():
    return "Suceeded"

@app.route('/addevent', methods = ['POST', 'GET'])
def add_event():
    if request.method == 'POST':
        ret = "Event Added"
        name = request.form['Event Name']
        data = {
            'organization': request.form['Organization'],
            'location': request.form['Location'],
            'start': request.form['Start Time'],
            'end': request.form['End Time'],
            'details':  request.form['Description'],
            'date': request.form['Date']
            }
        db.child('Freefood').child(name).set(data)
        return ret
    else:
        print("tring to redirect")
        print(url_for('static', filename = 'add_event.html'))
        return redirect(url_for('static', filename='add_event.html'))

@app.route('/deleteevent', methods = ['POST', 'GET'])
def delete_event():
    try:
        if request.method == 'POST':
            ret = "Event Deleted"
            name = request.form['Event Name']
            """
            data = {
                'organization': request.form['Organization'],
                'location': request.form['Location'],
                'start': request.form['Start Time'],
                'end': request.form['End Time'],
                'details':  request.form['Description'],
                'date': request.form['Date']
                }
            in_db = db.child('Freefood').child(name).get().val()
            """
            db.child('Freefood').child('test').remove()
            return "Deleted event %s" % name
        else:
            return redirect(url_for('static', filename='delete_event.html'))
    except Exception as e:
        return "Encountered an error while deleting %s" % e


@app.route('/getrecipe/<food_name>')
def get_recipe(food_name):
    try:
        #filter the ingredients by what's needed in the recipe
        def food(name, ingredients, description):
            return locals()
        recipes = db.child('Recipes').get().val()
        recipes = [food(k, {a:b for a, b in recipes[k].items() if a.lower() != "description"}, 
                        recipes[k].get('Description', recipes[k].get('description', "")))
                   for k in recipes if filters(k) == filters(food_name)]
        if not recipes:
            return "[]"
        else:
            return json.dumps(recipes[0])
    except Exception as e:
        return ("Failed to get recipe: %s" % e)


@app.route('/getstore/<input_str>')
def get_stores(input_str):
    try:
        food_name, lat, lon = input_str.split('_')
        lat = float(lat)
        lon = float(lon)

        #ALL THE LOGIC
        stores = db.child('Shops').get().val()

        def store(name, address, ingredients, ll = (0, 0)):
            return locals()
        stores = [store(stores[k]['name'], k, set(stores[k].keys()), 
                        tuple(map(float, stores[k]['geolocation'].split()))) for k in stores]

        stores.sort(key = lambda a: abs(lat - a['ll'][0]) + abs(lon - a['ll'][1]))
        stores = stores[:10]

        #filter the ingredients by what's needed in the recipe
        def food(name, ingredients, description):
            return locals()
        recipes = db.child('Recipes').get().val()
        recipes = [food(k, {a:b for a, b in recipes[k].items() if a.lower() != "description"}, 
                        recipes[k].get('Description', recipes[k].get('description', "")))
                   for k in recipes if filters(k) == filters(food_name)]
        if not recipes:
            return "[]"
        else: recipes = recipes[0]

        ing = set(recipes['ingredients'].keys())
        
        results = []
        for s in stores:
            if not ing:
                break

            if not s['ingredients'].isdisjoint(ing):
                temp = s['ingredients'].intersection(ing)
                s['ingredients'] = ', '.join(temp)
                results.append(s)
                ing = ing.difference(temp)

        #if ing:
        #    return "[]"

        return json.dumps(results)
    except Exception as e:
        return ("Could not process your request, please give an input string "
                "of the format food name_latitude_longitude: %s" % e)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
