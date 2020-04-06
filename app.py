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
         session['user_id']=username
         return redirect('/pickup_station')
      else:
         return 'Login Failed'

@app.route('/pickup_station')
def view():
   if('user_id' in session):
      return render_template('stations.html',userid=session['user_id'])
   else:
      return redirect('/login')


@app.route('/bike_select',methods=['POST'])
def stations():
    if('user_id' not in session):
       return('Invalid Method')
    if(request.method=='POST'):
        form=request.form
        s=form['station']
        session['station']=s
        mydb = mysql.connector.connect(**config)
        mycursor = mydb.cursor()
        mycursor.execute("SELECT number_plate,model_name from vehicles WHERE number_plate in (SELECT number_plate from location where station_id=(SELECT station_id from station where station_name=%s))",(s,))
        result=[]
        for x in mycursor:
           result.append(list(x))
        return render_template('vehicles.html',name=s,table=result)

@app.route('/book_process/<np>/<bike>')
def displaybookedvehicle(np,bike):
   print("Got ",np," of ",bike)
   return redirect('/ride')

@app.route('/ride')
def ridevehicle():
   if('station' in session):
      return render_template('ride.html',station=session['station'])
   else:
      return redirect('/login')

@app.route('/agent_login')
def agent_login():
   return render_template('agent_login.html')

@app.route('/agent_validate', methods=['POST'])
def agent_checktable():
   if(request.method == "POST"):
      details=request.form
      username=details['user']
      password=details['pass']
      s_id=details['s_id']
      mydb = mysql.connector.connect(**config)
      mycursor = mydb.cursor()
      mycursor.execute("SELECT name from agent WHERE name =%s", (username,))
      checker=mycursor.fetchone()
      if(checker==None):
         message = Markup("<p>Sorry Invalid Username !</p>")
         flash(message)
         return redirect(url_for('agent_login'))
      mycursor.execute("SELECT password from agent WHERE name =%s", (username,))
      passwordchecker=mycursor.fetchone()[0]
      mycursor.execute("SELECT station_id from agent WHERE name =%s", (username,))
      idchecker=mycursor.fetchone()[0]
      mycursor.close()
      if(checker==password and int(idchecker)==int(s_id)):  #need to redirect to something else! :)
         session['agent']=username
         return redirect('/agent/requests')
      else:
         mydb = mysql.connector.connect(**config)
         mycursor = mydb.cursor()
         mycursor.execute("SELECT * FROM agent")
         for x in mycursor:
            print(x)
         return 'Login Failed'

@app.route('/agent/requests')
def agent_requests():
   return 'View requests'
   # agent must view requests in this requests
         
@app.route('/end_ride/<station>/<distance>/<time>')
def ending_ride(station,distance,time):
   time=time[-4:]
   print(station,distance,time)
   return render_template("endride.html",username=session['user_id'],start_station=session['station'],distance=distance,end_station=station,time=time)

@app.route('/payment/<distance>/<time>')
def payment(distance,time):
   if(request.method == "POST"):
         details=request.form
         username=details['user']
         total_cost=distance * 3 + time * 0.5
         mydb = mysql.connector.connect(**config)
         mycursor = mydb.cursor()
         mycursor.execute("SELECT amount FROM users WHERE name = %s",(username,))
         checker=mycursor.fetchone()[0]
         mycursor.close()
         if(total_cost-checker > 500): #assuming 500 to be minimum balance
            return redirect('/two_mode')
         else:
            return redirect('/one_mode')

@app.route('/two_mode')
def payment_two_modes():
      if(request.method == "POST"):
         details=request.form
         username=details['user']
         mydb = mysql.connector.connect(**config)
         mycursor = mydb.cursor()
         mycursor.execute("SELECT * FROM ride")

@app.errorhandler(404)
def resource_not_found(e):
   return redirect(url_for('login'))

if __name__ == '__main__':
   app.secret_key = os.environ.get('secret_key')
   app.config['SESSION_TYPE'] = 'filesystem'
   # sess.init_app(app)
   app.run(debug=True,port=2011)
