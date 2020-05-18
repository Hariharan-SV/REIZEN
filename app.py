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
import math
import datetime
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

names={"saravanampatti":[0,33],"kurudampalayam":[2,10],"ashokapuram":[3,16],"gks":[4,29],"thudiyalur":[5,4],"chinnavedampatti":[5,21],"kumarasamyavanue":[6,13],
         "coimbatorenorth":[8,4],"koundampalayam":[8,8],"gandhipuram":[10,14],"ganapathy":[10,21],"neelambur":[10,33],"sivanandhacolony":[11,7],"saibabacolony":[12,1],"ganapathypudhur":[12,19],"womenspolytechnic":[14,16],
         "rspuram":[16,0],"peelamedu":[16,24],"hopes":[16,30],"lakshmimills":[18,16],"gandhipark":[22,0],"annastatue":[19,10],"airport":[21,32],"railwaystation":[30,8],"fivecorner":[32,1],"ramanathapuram":[19,24],
         "neelikonampalayam":[31,37],"ukkadam":[38,1],"singanallur":[38,21],"ondiputhur":[38,30]}
otp=0
SESSION_TYPE = 'memcache'

app=Flask(__name__)
app.static_folder='static'
app.secret_key = os.environ.get('secret_key')
app.config['SESSION_TYPE'] = 'filesystem'

def clearsession():
   temp=list(session.keys())
   print(temp)
   for key in temp:
      if(key != 'user_id'):
         print(key)
         session.pop(key)

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
      mycursor.execute("SELECT password,amount from users WHERE name =%s", (username,))
      checker=mycursor.fetchone()
      mycursor.close()
      if(checker[0]==password):
         resp = make_response(render_template('login.html'))
         session['user_id'] = username
         session['reizen_cash'] = int(checker[1])
         return redirect('/user_main')
      else:
         return 'Login Failed'

@app.route('/user_main')
def main_login_page():
   if(session is not None and 'user_id' in session):
      mydb = mysql.connector.connect(**config)
      mycursor = mydb.cursor()
      mycursor.execute("SELECT amount from users where name=%s",(session['user_id'],))
      session['reizen_cash']=mycursor.fetchone()[0]
      return render_template('mainloginpage.html',name=session['user_id'], amount=session['reizen_cash'])
   else:
      return redirect('/login')

@app.route('/pickup_station')
def view():
   if('user_id' in session):
      return render_template('stations.html',userid=session['user_id'])
   else:
      return redirect('/login')

@app.route('/user_history')
def history():
   if('user_id' not in session):
      return redirect('/login')
   username=session['user_id']
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("SELECT trip_id,start_station,end_station,start_time,end_time,amount FROM trip WHERE name=%s AND mode='YES'",(username,))
   result=[]
   for x in mycursor:
      result.append(x)
   print(result)
   return render_template('gobackpage.html',table=result,name=session['user_id'])

@app.route('/bike_select',methods=['POST'])
def stations():
    if('user_id' not in session):
      return redirect('/login')
    if(request.method=='POST'):
        form=request.form
        s=form['station']
        session['station']=s.lower()
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
      mydb = mysql.connector.connect(**config)
      mycursor = mydb.cursor()
      mycursor.execute("SELECT validity FROM booking WHERE name=%s",(session['user_id'],))
      validity=mycursor.fetchone()[0]
      if(validity=="YES"):
         print("Got ",np," of ",bike)
         mycursor.execute("DELETE FROM booking WHERE name=%s",(session['user_id'],))
         mydb.commit()
         return redirect('/ride')
      else:
         mycursor.execute("SELECT otp,time FROM booking WHERE name=%s",(session['user_id'],))
         value=mycursor.fetchone()
         otp=int(value[0])
         time_now=str(value[1])
         return render_template('waitpage.html',name=session['user_id'],station=session['station'],numberplate=np,bike=bike,otp=otp,time=time_now)
   else:
      otp=random.randrange(1000,9999,1)
      time_now=time.strftime('%y/%m/%d %H:%M:%S')
      mycursor.execute("UPDATE vehicles SET availabity='NO' WHERE number_plate=%s",(np,))
      mycursor.execute("INSERT INTO booking VALUES(%s,%s,%s,%s,%s,%s)",(session['user_id'],np,otp,time_now,"SINGLE","NO",))
      mydb.commit()
      return redirect('/book_process/'+np+'/'+bike)

@app.route('/ride')
def ridevehicle():
   global names
   if('station' in session):
      mydb = mysql.connector.connect(**config)
      mycursor = mydb.cursor()
      mycursor.execute("SELECT cur_latitude, cur_longtitude FROM ride WHERE name=%s",(session['user_id'],))
      data=mycursor.fetchone()
      return render_template('ride.html',x=data[1],y=data[0])
   else:
      return redirect('/login')

@app.route('/report/<x>/<y>')
def updateridetable(x,y):
   if('station' in session):
      print(x,y)
      mydb = mysql.connector.connect(**config)
      mycursor = mydb.cursor()
      mycursor.execute("SELECT cur_latitude,cur_longtitude FROM ride where name=%s",(session['user_id'],))
      data=mycursor.fetchone()
      mycursor.execute("UPDATE ride SET prev_latitude=%s, prev_longtitude=%s WHERE name=%s",(data[0],data[1],session['user_id'],))
      mydb.commit()
      distance=abs(int(data[0])-int(x))+abs(int(data[1])-int(y))
      mycursor.execute("UPDATE ride SET cur_latitude=%s, cur_longtitude=%s, distance=distance+%s WHERE name=%s",(x,y,distance,session['user_id'],))
      mydb.commit()
      return "Success"

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
         return redirect('/agent_main')
      else:
         mydb = mysql.connector.connect(**config)
         mycursor = mydb.cursor()
         print(passwordchecker,password,s_id,idchecker)
         mycursor.execute("SELECT * FROM agent")
         for x in mycursor:
            print(x)
         return 'Login Failed'

@app.route('/agent_main')
def agent_mainpage():
   if('agent' not in session):
      return redirect('/agent_login')
   return render_template('agent_mainpage.html',name=session['agent'])

@app.route('/recharge_cash',methods=['GET','POST'])
def recharge():
   if('agent' not in session):
      return redirect('/agent_login')
   if(request.method == 'POST'):
      details=request.form
      username=details['user']
      amount=details['amount']
      mydb = mysql.connector.connect(**config)
      mycursor = mydb.cursor()
      mycursor.execute("UPDATE users SET amount=amount+%s WHERE name=%s",(int(amount),username,))
      mydb.commit()
   return render_template('recharge.html')

@app.route('/agent_requests')
def agent_requests():
   if('agent' not in session):
      return redirect('/agent_login')
   s=session['agent_station']
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("SELECT name,number_plate,time,validity FROM booking WHERE validity='NO' AND number_plate in (SELECT number_plate FROM location where station_id=%s)",(int(s),))
   result=[]
   for x in mycursor:
      result.append(list(x))
   return render_template('agentrequests.html',table=result)
   #return 'View requests'
   #agent must view requests in this requests

@app.route('/payment_processing')
def payment_processing():
   if('user_id' not in session):
      return redirect('/login')
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("SELECT * FROM trip WHERE name=%s",(session['user_id'],))
   data=mycursor.fetchall()
   print("\n\n",data)
   if(data[len(data)-1][-1]=='NO'):
      return render_template('paymentwaiting.html')
   else:
      clearsession()
      return render_template('thankyou.html',name=session['user_id'])

@app.route('/delete_booking')
def delete_booking():
   if('station' not in session):
      return redirect('/user_main')
   if('user_id' not in session):
      return redirect('/login')
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   try:
      mycursor.execute("UPDATE vehicles SET availabity='YES' WHERE number_plate=(SELECT number_plate FROM booking WHERE name=%s)",(session['user_id'],))
      mycursor.execute("DELETE FROM booking WHERE name=%s",(session['user_id'],))
      mydb.commit()
   except:
      mydb.rollback()
      return redirect('/delete_booking')
   session['station']=None
   return render_template('cancel_booking.html')

@app.route('/update_booking/<username>/<otp>')
def update_user_validity(username,otp):
   if('agent' not in session):
      return redirect('/agent_login')
   s=session['agent_station']
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("SELECT otp from booking where name=%s",(username,))
   data = mycursor.fetchone()
   if( int(data[0]) != int(otp)):
      return redirect('/agent_requests')
   try:
      mycursor.execute("UPDATE booking SET validity=%s WHERE name=%s",("YES",username,))
      mydb.commit()
   except:
      mydb.rollback()
      return redirect('/update_booking/'+username+'/'+otp)
   global names
   mycursor.execute("SELECT station_name FROM station WHERE station_id=%s",(s,))
   s_name=mycursor.fetchone()[0]
   l1=list(names[s_name])
   lat=l1[0]
   longi=l1[1]
   mycursor.execute("SELECT number_plate FROM booking WHERE name=%s",(username,))
   result=mycursor.fetchone()
   mycursor.execute("INSERT INTO ride(name,number_plate,start_time,prev_latitude,prev_longtitude,cur_latitude,cur_longtitude,distance,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ",(username,result[0],str(time.strftime('%y/%m/%d %H:%M:%S')),lat,longi,lat,longi,0,"NO",))
   mydb.commit()
   mycursor.close()
   return redirect('/agent_requests')

@app.route('/end_ride/<station>/')
def ending_ride(station):
   if('user_id' not in session):
      return redirect('/login')
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("SELECT * FROM ride where name=%s",(session['user_id'],))
   if(mycursor.fetchone() is None):
      if('distance' in session and 'amt' in session and 'tripid' in session and 'np' in session and 'end_station' in session and 'station' in session and 'time' in session):
         return render_template("endride.html",username=session['user_id'],start_station=session['station'],distance=session['distance'],end_station=session['end_station'],time=session['time'],amount=session['amt'])
      else:
         return 'if you think that a problem occured here while ending your ride we apologise for your inconvienience'
   end_time= time.strftime('%y/%m/%d %H:%M:%S')
   mycursor.execute("SELECT distance,start_time FROM ride WHERE name=%s",(session['user_id'],))
   data=mycursor.fetchone()
   distance = int(data[0])*10
   secs = datetime.datetime.strptime(end_time,'%y/%m/%d %H:%M:%S') - datetime.datetime.strptime(str(data[1]),'%Y-%m-%d %H:%M:%S')
   secs = int(secs.total_seconds())
   print(secs,type(secs))
   total_cost = int(distance) * 0.07 + int(secs) * 0.05
   mycursor.execute("SELECT name,number_plate,start_time from ride where name=%s",(session['user_id'],))
   data=mycursor.fetchone()
   mycursor.execute("INSERT INTO trip(name,number_plate,start_time,end_time,start_station,end_station,distance,amount,mode) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(session['user_id'],data[1],data[2],end_time,session['station'],station,distance,total_cost,"NO",))
   mydb.commit()
   mycursor.execute("DELETE FROM ride where name=%s",(session['user_id'],))
   mydb.commit()
   print(session['user_id'],data[1],data[2],secs)
   mycursor.execute("SELECT trip_id FROM trip WHERE name=%s AND number_plate=%s AND start_time=%s AND end_time=%s",(session['user_id'],data[1],data[2],end_time,))
   tid=int(mycursor.fetchone()[0])
   session['tripid']=tid
   session['np'] = data[1]
   session['end_station']=station
   session['distance'] = distance
   session['time'] = secs
   #print(station,distance,time1)
   return render_template("endride.html",username=session['user_id'],start_station=session['station'],distance=session['distance'],end_station=session['end_station'],time=session['time'],amount=math.ceil(total_cost))

@app.route('/payment/<amount>')
def payment(amount):
   if('user_id' not in session):
      return redirect('/login')
   else:
      s=session['user_id']
      mydb = mysql.connector.connect(**config)
      mycursor = mydb.cursor()
      mycursor.execute("SELECT amount FROM users WHERE name = %s",(s,))
      checker=mycursor.fetchone()[0]
      mycursor.close()
      amt=math.ceil(float(amt))
      if(int(checker)-amt > 50): #assuming 50 to be minimum balance
         return redirect('/two_mode')
      else:
         return redirect('/one_mode')

@app.route('/two_mode')
def payment_two_modes():
   if('user_id' not in session):
      return redirect('/login')
   username=session['user_id']
   return render_template('twomodepayment.html',name=username)

@app.route('/one_mode')
def payment_one_mode():
   if('user_id' not in session):
      return redirect('/login')
   username=session['user_id']
   return render_template('onemodepayment.html',name=username)

@app.route('/agent_cash')
def ack_cash():
   if('agent' not in session):
      return redirect('/agent_login')
   mydb=mysql.connector.connect(**config)
   mycursor=mydb.cursor()
   s=session['agent_station']
   mycursor.execute("SELECT station_name FROM station WHERE station_id=%s",(s,))
   stn=mycursor.fetchone()[0]
   mycursor.execute("SELECT trip_id,name,number_plate,start_station,end_station,amount FROM trip WHERE (mode='NO' AND end_station=%s)",(stn,))
   result=[]
   for x in mycursor:
      result.append(x)
   return render_template('cash_pay.html',table=result)

@app.route('/agent_end/<tid>/<username>/<np>/<end_station>/<amt>')
def end_user_trip_by_agent(tid,username,np,end_station,amt):
   if('agent' not in session):
      return redirect('/agent_login')
   mydb=mysql.connector.connect(**config)
   mycursor=mydb.cursor()
   mycursor.execute("UPDATE vehicles SET availabity='YES' WHERE number_plate=%s",(np,))
   mydb.commit()
   mycursor.execute("UPDATE location SET station_id=(SELECT station_id from station where station_name=%s) WHERE number_plate=%s",(end_station,np,))
   mydb.commit()
   mycursor.execute("UPDATE trip SET mode='YES' WHERE trip_id=%s",(int(tid),))
   mydb.commit()
   return redirect('/agent_cash')

@app.route('/reduce_reizen_amount')
def reducereizencash():
   if('user_id' not in session):
      return redirect('/login')
   username=session['user_id']
   amt=session['amt']
   tid=session['tripid']
   mydb = mysql.connector.connect(**config)
   mycursor = mydb.cursor()
   mycursor.execute("UPDATE users SET amount=amount-%s WHERE name=%s",(amt,username,))
   mydb.commit()
   mycursor.execute("UPDATE vehicles SET availabity='YES' WHERE number_plate=%s",(session['np'],))
   mydb.commit()
   mycursor.execute("UPDATE location SET station_id=(SELECT station_id from station where station_name=%s) WHERE number_plate=%s",(session['end_station'],session['np'],))
   mydb.commit()
   mycursor.execute("UPDATE trip SET mode='YES' WHERE trip_id=%s",(tid,))
   mydb.commit()
   clearsession()
   return render_template('thankyou.html',name=username)

@app.route('/logout')
def logout():
      temp=list(session.keys())
      for key in temp:
            session.pop(key)
      return redirect('/login')

@app.errorhandler(404)
def resource_not_found(e):
   return redirect('/login')

if __name__ == '__main__':
   app.run()
