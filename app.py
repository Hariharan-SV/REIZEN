# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 19:04:17 2020

@author: DELL
"""

from flask import Flask,request,render_template,make_response
from flask import Markup,flash,session,redirect,url_for
# from flask_session import Session
import mysql.connector
from runenv import load_env
import os
import ast
import json
load_env()

#config= os.environ.get('config')
user= os.environ.get('user')
host= os.environ.get('host')
passwd= os.environ.get('passwd')
database= os.environ.get('database')
config = {
'user':user,
'host':host,
'passwd':passwd,
'database':database
}

SESSION_TYPE = 'memcache'

app=Flask(__name__)
app.static_folder='static'
# sess = Session()


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
      mydb = mysql.connector.connect(**config)
      mycursor = mydb.cursor()
      mycursor.execute("SELECT name from users WHERE name =%s", (username,))
      checker=mycursor.fetchone()
      if(checker!=None and checker[0]==username):
         message = Markup("<p>Sorry that name is already taken !</p>")
         flash(message)
         return redirect(url_for('signup'))
      if(password==retypepass):
         mycursor.execute("INSERT INTO users(name,password) VALUES (%s, %s)", (username, password))
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
      mydb = mysql.connector.connect(**config)
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
         resp = make_response(render_template('login.html'))
         # resp.set_cookie('userID', username)
         session['user_id']=username

         #return resp
         return redirect('/pickup_station')
         #fvWTyF1pbV
      else:
         return 'Login Failed'


@app.route('/start_station',methods=['POST'])
def stations():
    if(request.method=='POST'):
        form=request.form
        s=form['station']
        print("Station is ",s)
        return render_template('startstation.html',name=s)

@app.route('/pickup_station')
def view():
   if('user_id' in session):
      return render_template('stations.html',userid=session['user_id'])
   else:
      return redirect('/login')

@app.route('/book')
def bookbike():
   result=[["TN72BJ6087","TVS Scooty"],["TN72AM8262","TVS Star"]]
   return render_template('vehicles.html',table=result)

@app.route('/book_process/<name>', methods=['POST'])
def displaybookedvehicle(name):
   if(request.method == "POST"):
      print("Before")
      print("Got ",name)
      return str(name)

@app.route('/ride')
def ridevehicle():
   if('station' in session):
      return render_template('ride.html',station=session['station'])
   else:
      return redirect('/login')

@app.errorhandler(404)
def resource_not_found(e):
   return redirect(url_for('login'))

if __name__ == '__main__':
   app.secret_key = os.environ.get('secret_key')
   app.config['SESSION_TYPE'] = 'filesystem'
   # sess.init_app(app)
   app.run(debug=True,port=2011)
