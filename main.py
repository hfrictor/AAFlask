import firebase_admin
import requests
import json
import logging
from itsdangerous import exc
import datetime
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, Form, SelectField
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, Email
from os.path import exists
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
from firebase_admin import auth
from flask_ckeditor import CKEditor
from flask_ckeditor import CKEditorField


#Line to have better command line logging with flask
logging.basicConfig(level=logging.DEBUG)

#Create a flask instance
app = Flask(__name__)
ckeditor = CKEditor(app)
app.config['SECRET_KEY'] = "keywillbechanged"

#Intitializing Firestore using google firestore
cred = credentials.Certificate("smart-saucer-8f12f-firebase-adminsdk-51ili-841acf87b8.json")

FIREBASE_WEB_API_KEY = "AIzaSyDIx7oHNxIdG1XSSdRP5DESjkPphL-Oxas"
rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://smart-saucer-8f12f-default-rtdb.firebaseio.com'
})

dbStore = firestore.client()
print("Successfully setup Firebase at "+ str(datetime.datetime.now()))

#Creating user declerations
global first_name
global last_name
global user_email
global is_logged_in


global saucers_dictionary
saucers_dictionary = {}



#Creating a form class

class Loginform(FlaskForm):
    email = StringField("Email", validators=[Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    login = SubmitField("Login")

class Registerform(FlaskForm):
    firstname = StringField("Firstname", validators=[DataRequired()])
    lastname = StringField("Lastname", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirmpass = PasswordField("Confirm Password", validators=[DataRequired()])
    register = SubmitField("Register")


class Profileform(FlaskForm):
    firstname = StringField("Firstname", validators=[DataRequired()])
    lastname = StringField("Lastname", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Old Password", validators=[DataRequired()])
    newpass = PasswordField("New Password", validators=[DataRequired()])
    confirmpass = PasswordField("Confirm New Password", validators=[DataRequired()])
    
    userbio = CKEditorField('User Bio', validators=[DataRequired()])

    savechange = SubmitField("Save Changes")


#Create a route decorator
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/smartsaucer/<first_name>')
def smartsaucer(first_name):
    get_saucers()

    return render_template("MainScreens/smartsaucer.html", 
                            first_name = first_name, 
                            saucers_dictionary = saucers_dictionary)



def sign_in_with_email_and_password(email: str, password: str, return_secure_token: bool = True):
    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": return_secure_token
    })

    r = requests.post(rest_api_url,
                      params={"key": FIREBASE_WEB_API_KEY},
                      data=payload)

    return r.json()



#Create Login Page 
@app.route('/login', methods=['GET', 'POST'])
def login():
    global first_name
    global last_name
    global user_email
    global is_logged_in

    global recents_library_images
    email = None
    password = None
    login_form = Loginform()

    if login_form.validate_on_submit():
        try:
            token = sign_in_with_email_and_password(email=login_form.email.data, password=login_form.password.data)
            if token['registered'] == True:
                usr_ref = dbStore.collection('Users').document(login_form.email.data)
                usr = usr_ref.get()
                if usr.exists:
                    usr.to_dict()
                    first_name = usr.get('firstname')
                    last_name = usr.get('lastname')
                    user_email = usr.get('email')
                    is_logged_in = True
                    get_saucers()
                    print(saucers_dictionary)
                    return redirect(url_for('smartsaucer', 
                                            first_name = first_name, 
                                            saucers_dictionary = saucers_dictionary))
                else:
                    return render_template("Authentication/login.html", 
                                            email = email, 
                                            password = password, 
                                            login_form = login_form)
            
        except:
            return render_template("Authentication/login.html", 
                                        email = email, 
                                        password = password, 
                                        login_form = login_form)

    return render_template("Authentication/login.html", 
                                        email = email, 
                                        password = password, 
                                        login_form = login_form)

#Create Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():

    global first_name
    global last_name
    global user_email
    global is_logged_in

    firstname = None
    lastname = None
    email = None
    password = None
    confirmpass = None
    register_form = Registerform()
        

    if register_form.validate_on_submit():
        try:
            #New user initializations on register
            firstname = str(register_form.firstname.data)
            lastname = str(register_form.lastname.data)
            currentPassword = str(register_form.password.data)
            newPassword = ""
            email = str(register_form.email.data)

            auth.create_user(email = register_form.email.data, password = register_form.password.data)
            usr_ref = dbStore.collection('Users').document(register_form.email.data)
            usr_ref.set({
                'firstname': firstname,
                'lastname': lastname,
                'currentPassword': currentPassword,
                'newPassword': newPassword,
                'email': email
            })

            token = sign_in_with_email_and_password(email=register_form.email.data, password=register_form.password.data)

            if token['registered'] == True:
                usr_ref = dbStore.collection('Users').document(register_form.email.data)
                usr = usr_ref.get()
                if usr.exists:
                    usr.to_dict()
                    first_name = usr.get('firstname')
                    last_name = usr.get('lastname')
                    user_email = usr.get('email')
                    is_logged_in = True
                    get_saucers()
                    return redirect(url_for('smartsaucer', 
                                            first_name = first_name, 
                                            saucers_dictionary = saucers_dictionary))
                else:
                    return render_template("Authentication/register.html", 
                                            firstname = firstname, 
                                            lastname = lastname, 
                                            email = email, 
                                            password = password, 
                                            confirmpass = confirmpass,
                                            register_form = register_form)
        except:
            return render_template("Authentication/register.html", 
                                    firstname = firstname, 
                                    lastname = lastname, 
                                    email = email, 
                                    password = password, 
                                    confirmpass = confirmpass,
                                    register_form = register_form)


    return render_template("Authentication/register.html", 
                                    firstname = firstname, 
                                    lastname = lastname, 
                                    email = email, 
                                    password = password, 
                                    confirmpass = confirmpass,
                                    register_form = register_form)



def get_saucers():
    global saucers_dictionary
    saucers_dictionary = {}

    for i in range(1,9):
        
        location = db.reference('/SS2021-000'+str(i)+'/Diagnostic/location')
        serial_num = db.reference('/SS2021-000'+str(i)+'/Diagnostic/hardware')
        seven = db.reference('/SS2021-000'+str(i)+'/Pizza%20Throughput/7/COUNT')
        ten = db.reference('/SS2021-000'+str(i)+'/Pizza%20Throughput/10/COUNT')
        twelve = db.reference('/SS2021-000'+str(i)+'/Pizza%20Throughput/12/COUNT')
        fourteen = db.reference('/SS2021-000'+str(i)+'/Pizza%20Throughput/14/COUNT')
        ping_date = db.reference('/SS2021-000'+str(i)+'/Diagnostic/update')

        try:
            data = { "location" : location.get(),
                    "serial_num" : serial_num.get(),
                    "seven" : seven.get(),
                    "ten" : ten.get(),
                    "twelve" : twelve.get(),
                    "fourteen" : fourteen.get(),
                    "ping_date" : ping_date.get()}
            if None in data:
                print(i)
            else:
                saucers_dictionary[i] = data
                print(i)
                print(saucers_dictionary)
        except:
            print("Couldnt Get the Data for: "+ str(i))
        

    return(saucers_dictionary)


#Custom error pages
@app.errorhandler(404)
def page_not_found(e):
    return render_template("Errors/404.html"), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template("Errors/500.html"), 500