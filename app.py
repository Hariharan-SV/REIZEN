# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 19:04:17 2020

@author: DELL
"""

from flask import Flask,request,render_template
from flask import Markup,flash,session,redirect,url_for
from flask_session import Session
import mysql.connector
from runenv import load_env
import os
load_env()
user= os.environ.get('user')
host= os.environ.get('host')
passwd= os.environ.get('passwd')
database= os.environ.get('database')

SESSION_TYPE = 'memcache'

app=Flask(__name__)
app.static_folder='static'
sess = Session()


@app.route('/login')
def login():
   return render_template('login.html')

@app.route('/signup')
def signup():
   return render_template('signup.html')

@app.route('/update', methods=['GET', 'POST'])
def updatetable():
   if(request.method == "POST"):
      details=request.form
      username=details['user']
      password=details['pass']
      retypepass=details['retype-pass']
      mydb = mysql.connector.connect(host,user,passwd,database)
      mycursor = mydb.cursor()
      mycursor.execute("SELECT name from users WHERE name =%s", (username,))
      checker=mycursor.fetchone()
      if(checker!=None and checker[0]==username):
         message = Markup("<p>Sorry that name is already taken !</p>")
         flash(message)
         return redirect(url_for('signup'))
      if(password==retypepass):
         mycursor.execute("INSERT INTO users(name,password) VALUES (%s, %s)", (username, passwd))
         mydb.commit()
         mycursor.close()
         message = Markup("<p>Account Created!</p>")
         flash(message)
         return redirect(url_for('signup'))
      else:
         message = Markup("<p>Passwords Mismatch!</p>")
         flash(message)
         return redirect(url_for('signup'))
   return render_template('signup.html')

@app.route('/validate', methods=['POST'])
def checktable():
   if(request.method == "POST"):
      details=request.form
      username=details['user']
      password=details['pass']
      mydb = mysql.connector.connect(host,user,passwd,database)
      mycursor = mydb.cursor()
      mycursor.execute("SELECT name from users WHERE name =%s", (username,))
      checker=mycursor.fetchone()
      if(checker==None):
         message = Markup("<p>Sorry Invalid Username !</p>")
         flash(message)
         return redirect(url_for('login'))
      mycursor.execute("SELECT password from users WHERE name =%s", (username,))
      checker=mycursor.fetchone()[0]
      mycursor.close()
      if(checker==password):
         return 'Login Success'
      else:
         return 'Login Failed'

@app.errorhandler(404)
def resource_not_found(e):
   return redirect(url_for('login'))

if __name__ == '__main__':
   app.secret_key = os.environ.get('secret_key')
   app.config['SESSION_TYPE'] = 'filesystem'
   sess.init_app(app)
   app.run(debug=True)
