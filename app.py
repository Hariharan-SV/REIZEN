# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 19:04:17 2020

@author: DELL
"""

from flask import Flask,request,render_template,make_response
from flask import Markup,flash,session,redirect,url_for
import time
import mysql.connector
from runenv import load_env
import os
import ast
import json
import random
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

otp=0
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
        mycursor.execute("SELECT number_plate,model_name from vehicles WHERE availabity='YES' AND number_plate in (SELECT number_plate from location where station_id=(SELECT station_id from station where station_name=%s))",(s,))
        result=[]
        for x in mycursor:
           result.append(list(x))
        return render_template('vehicles.html',name=s,table=result)

@app.route('/book_process/<np>/<bike>')
def displaybookedvehicle(np,bike):
   global otp
   if('station' not in session):
      return redirect('/bike_select')
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("SELECT name FROM booking WHERE name=%s",(session['user_id'],))
   if(mycursor.fetchone() is not None):
      mycursor.execute("SELECT validity FROM booking WHERE name=%s",(session['user_id'],))
      validity=mycursor.fetchone()[0]
      if(validity=="YES"):
         print("Got ",np," of ",bike)
         mycursor.execute("DELETE FROM booking WHERE name=%s",(session['user_id'],))
         mydb.commit()
         return redirect('/ride')
      else:
         mycursor.execute("SELECT otp FROM booking WHERE name=%s",(session['user_id'],))
         otp=int(mycursor.fetchone()[0])
         return render_template('waitpage.html',name=session['user_id'],station=session['station'],numberplate=np,bike=bike,otp=otp)
   else:
      otp=random.randrange(1000,9999,1)
      time_now=time.strftime('%d/%m/%y %H:%M:%S')
      mycursor.execute("UPDATE vehicles SET availabity='NO' WHERE number_plate=%s",(np,))
      mycursor.execute("INSERT INTO booking VALUES(%s,%s,%s,%s,%s,%s)",(session['user_id'],np,otp,time_now,"SINGLE","NO",))
      mydb.commit()
      return redirect('/book_process/'+np+'/'+bike)

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
      password=details['pass']
      username=password
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
      if(passwordchecker.lower()==password.lower() and int(idchecker)==int(s_id)):  #need to redirect to something else! :)
         session['agent']=username
         session['agent_station']=s_id
         return redirect('/agent_requests')
      else:
         mydb = mysql.connector.connect(**config)
         mycursor = mydb.cursor()
         print(passwordchecker,password,s_id,idchecker)
         mycursor.execute("SELECT * FROM agent")
         for x in mycursor:
            print(x)
         return 'Login Failed'

@app.route('/agent_requests')
def agent_requests():
   s=session['agent_station']
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("SELECT * FROM booking WHERE number_plate in (SELECT number_plate FROM location where station_id=%s)",(int(s),))
   result=[]
   for x in mycursor:
      result.append(list(x))
   return render_template('agentrequests.html',table=result)
   #return 'View requests'
   #agent must view requests in this requests

@app.route('/update_booking/<username>')
def update_user_validity(username):
   s=session['agent_station']
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   try:
      mycursor.execute("UPDATE booking SET validity=%s WHERE name=%s",("YES",username,))
      mydb.commit()
   except:
      print("Failed")
   names={"saravanampatti":[0,33],"kurudampalayam":[2,10],"ashokapuram":[3,16],"gks":[4,29],"thudiyalur":[5,4],"chinnavedampatti":[5,21],"kumarasamyavanue":[6,13],
         "coimbatorenorth":[8,4],"koundampalayam":[8,8],"gandhipuram":[10,14],"ganapathy":[10,21],"neelambur":[10,33],"sivanandhacolony":[11,7],"saibabacolony":[12,1],"ganapathypudhur":[12,19],"womenspolytechnic":[14,16],
         "rspuram":[16,0],"peelamedu":[16,24],"hopes":[16,30],"lakshmimills":[18,16],"gandhipark":[22,0],"annastatue":[19,10],"airport":[21,32],"railwaystation":[30,8],"fivecorner":[32,1],"ramanathapuram":[19,24],
         "neelikonampalayam":[31,37],"ukkadam":[38,1],"singanallur":[38,21],"ondiputhur":[38,30]}
   mycursor.execute("SELECT station_name FROM station WHERE station_id=%s",(s,))
   s_name=mycursor.fetchone()[0]
   l1=list(names[s_name])
   lat=l1[0]
   longi=l1[1]
   mycursor.execute("SELECT number_plate,time FROM booking WHERE name=%s",(username,))
   result=[]
   for x in mycursor:
      result.append(list(x))
   try:
      mycursor.execute("INSERT INTO ride(name,number_plate,start_time,prev_latitude,prev_longitude,status) VALUES (%s,%s,%s,%s,%s,%s) ",(username,result[0],result[1],lat,longi,"NO"))
      mydb.commit()
   except:
      print("Failed")
   mycursor.execute("SELECT model_name FROM vehicles WHERE number_plate=%s",(result[0][0],))
   checker=mycursor.fetchone()[0]
   model=checker
   mycursor.close()
   return redirect('/agent_requests')

@app.route('/end_ride/<station>/<distance>/<time1>')   #second-to-second update the position of the rider
def ending_ride(station,distance,time1):
   time1=time1[-4:]
   sec=int(time1[2:])
   total_cost = int(distance) * 0.7 + sec * 0.5
   session['amt']=total_cost
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("SELECT name,number_plate,start_time from ride where name=%s",(session['user_id'],))
   data=mycursor.fetchone()
   end_time=time.strftime('%d/%m/%y %H:%M:%S')
   mycursor.execute("INSERT INTO trip(name,number_plate,start_time,end_time,start_station,end_station,distance,amount,mode) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(session['user_id'],data[1],data[2],end_time,session['station'],station,distance,time1,))
   mydb.commit()
   print(station,distance,time1)
   return render_template("endride.html",username=session['user_id'],start_station=session['station'],distance=distance,end_station=station,time=time1,amount=total_cost)

@app.route('/payment/<amount>')
def payment(amount):
         if('user_id' not in session):
                return 'Invalid method'
         else:
            s=session['user_id']
            mydb = mysql.connector.connect(**config)
            mycursor = mydb.cursor()
            mycursor.execute("SELECT amount FROM users WHERE name = %s",(s,))
            checker=mycursor.fetchone()[0]
            mycursor.close()
            amt=amount[:-2]
            amt=int(amt)
            if(int(checker)-amt > 500): #assuming 500 to be minimum balance
               return redirect('/two_mode')
            else:
               return redirect('/one_mode')

@app.route('/two_mode')
def payment_two_modes():
   username=session['user_id']
   return render_template('twomodepayment.html',name=username)

@app.route('/one_mode')
def payment_one_mode():
   username=session['user_id']
   return render_template('onemodepayment.html',name=username)

@app.route('/agent_cash')
def ack_cash():
   mydb=mysql.connector.connect(**config)
   mycursor=mydb.cursor()
   s=session['agent_station']
   mycursor.execute("SELECT station_name FROM station WHERE station_id=%s",(s,))
   stn=mycursor.fetchone()[0]
   mycursor.execute("SELECT trip_id,name,start_station,end_station,amount FROM trip WHERE (mode='NO' AND end_station=%s)",(stn,))
   result=[]
   for x in mycursor:
      result.append(x)
   return render_template('cash_pay.html',table=result)

@app.route('/agent_end/<tid>')
def end_user_trip_by_agent(tid):
   mydb=mysql.connector.connect(**config)
   mycursor=mydb.connect()
   mycursor.execute("UPDATE trip SET mode='YES' WHERE trip_id=%s",(tid,))
   return redirect('/agent_requests')

@app.route('/reduce_reizen_amount')
def reducereizencash():
   username=session['user_id']
   amt=session['amt']
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("UPDATE users SET amount=amount-%s WHERE name=%s",(amt,username,))
   mydb.commit()
   return render_template('thankyou.html',name=username)

@app.errorhandler(404)
def resource_not_found(e):
   return redirect(url_for('login'))

if __name__ == '__main__':
   app.secret_key = os.environ.get('secret_key')
   app.config['SESSION_TYPE'] = 'filesystem'
   # sess.init_app(app)
   app.run(debug=True,port=2011)
