# -*- coding: utf-8 -*-
import os
from sqlite3 import Timestamp
from flask import Flask
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask import redirect,url_for
import datetime
import matplotlib.pyplot as plt

current_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(current_dir, "projectdb.db") 
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

class Login(db.Model):
    __tablename__='Login'
    Username=db.Column(db.String,unique=True,primary_key=True)
    Password=db.Column(db.String,nullable=False)
    trackers = db.relationship('Trackers', backref='user',cascade="all, delete", lazy=True)


class Trackers(db.Model):
    __tablename__='Trackers'
    Id=db.Column(db.Integer,unique=True,autoincrement=True,primary_key=True)
    Name=db.Column(db.String,unique=True,nullable=False)
    Description=db.Column(db.String,nullable=False)
    TrackerType=db.Column(db.String,nullable=False)
    Settings=db.Column(db.String)
    User=db.Column(db.String,db.ForeignKey("Login.Username"),nullable=False)
    Last_Tracked=db.Column(db.String,unique=False,nullable=False)
    trackers_details = db.relationship('Tracker_logs', backref='tracker',cascade="all, delete", lazy=True)


class Tracker_logs(db.Model):
    __tablename__='Tracker_logs'
    T_id=db.Column(db.Integer,unique=True,autoincrement=True,primary_key=True)
    #Tracker_id=db.Column(db.Integer,db.ForeignKey("Trackers.Id"),nullable=False)
    Timestamp=db.Column(db.String,nullable=False)
    Tracker_name=db.Column(db.String,db.ForeignKey("Trackers.Name"),nullable=False)
    Value=db.Column(db.String,nullable=False)
    Notes=db.Column(db.String)

@app.route("/",methods=["GET","POST"])
def login_page():
    if request.method=="GET":
        return render_template("login.html")
    if request.method=="POST":
        username=request.form["user"]
        password=request.form["pass"]
        user=Login.query.filter_by(Username=username).first()
        if not user:
            return render_template("login_error.html")
        if user.Password!=password:
            return render_template("login_error.html")
        return redirect("/dashboard/{}".format(username))

@app.route("/sign_up",methods=["GET","POST"])
def sign_page():
    if request.method=="GET":
        return render_template("sign_up.html")
    if request.method=="POST":
        username=request.form["user"]
        password=request.form["pass"]
        user=Login.query.filter_by(Username=username).first()
        if not user:
            new_user=Login(Username=username,Password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")
        else:
            return render_template("sign_error.html")

@app.route("/dashboard/<usern>",methods=["GET","POST"])
def dashboard_page(usern):
    if request.method=="GET":
        tracker=Trackers.query.filter_by(User=usern).all()
        return render_template("dashboard.html",user=usern,trackers=tracker)        

@app.route("/tracker/<usern>/add",methods=["GET","POST"])
def add_tracker(usern):
    if request.method=="GET":
        return render_template("add_tracker.html",user=usern)
    if request.method=="POST":
        tracker_name=request.form["name"]
        description=request.form["desc"]
        tracker_type=request.form['trackers']
        settings=request.form["o1"]
        tracker=Trackers(Name=tracker_name,Description=description,TrackerType=tracker_type,Settings=settings,User=usern)
        try:
            db.session.add(tracker)
            db.session.commit()
        except:
            db.session.rollback()
        return redirect("/dashboard/{}".format(usern))

@app.route("/tracker/<usern>/<tname>/delete",methods=["GET","POST"])
def del_tracker(usern,tname):
    if request.method=="GET":
        tracker=Trackers.query.filter_by(Name=tname).first()
        db.session.delete(tracker)
        db.session.commit()
        return redirect("/dashboard/{}".format(usern))

@app.route("/tracker/<usern>/<tname>/log",methods=["GET","POST"])
def log_tracker(usern,tname):
    if request.method=="GET":
       now = datetime.datetime.now()
       ct=now.strftime('%Y-%m-%dT%H:%M')
       trackers=Trackers.query.filter_by(Name=tname).first()
       if trackers.TrackerType=="boolean":
           return render_template("add_log_bool.html",user=usern,tracker=trackers,timestamp=ct)   
       if trackers.TrackerType=="Multiple Choice":
           setting=trackers.Settings
           setting_list=list(setting.split(','))
           return render_template("add_log_mcq.html",settings=setting_list,user=usern,tracker=trackers,timestamp=ct)
       if trackers.TrackerType=="Time":
           return render_template("add_log_time.html",user=usern,tracker=trackers,timestamp=ct)
       return render_template("add_log.html",user=usern,tracker=trackers,timestamp=ct)
    if request.method=="POST": 
        cts=request.form["timestam"]
        note=request.form["notes"]
        value=request.form["val"]
        print(cts,note,value)
        logss=Tracker_logs.query.filter_by(Timestamp=cts).first()
        if logss:
            return render_template("Logging_error.html")
        log=Tracker_logs(Timestamp=cts,Tracker_name=tname,Value=value,Notes=note)
        db.session.add(log)
        db.session.commit()
        #tracker=Trackers.query.filter_by(User=usern).first()
        #tname=tracker.Name
        tracker=Trackers.query.filter_by(Name=tname).first()
        tracker_log=Tracker_logs.query.filter_by(Tracker_name=tname).all()
        time="0"
        for log in tracker_log:
            if log.Timestamp>time:
                time=log.Timestamp
        tracker.Last_Tracked=time
        db.session.commit()
        return redirect("/dashboard/{}".format(usern))
        #to be filled

@app.route("/tracker/<usern>/<tname>/edit",methods=["GET","POST"])
def edit_tracker(usern,tname): 
    if request.method=="GET":
        return render_template("edit_tracker.html",user=usern,tname=tname)
    if request.method=="POST":
        tracker_name=request.form["name"]
        description=request.form["desc"]
        settings=request.form["o1"] 
        trackers=Trackers.query.filter_by(Name=tname).first()
        trackerss=Trackers.query.filter_by(Name=tracker_name).first()
        if trackerss:
            return render_template("Tracker_error.html")
        trackers.Name=tracker_name
        trackers.Description=description
        trackers.Settings=settings
        db.session.commit()
        tracker=Trackers.query.filter_by(Name=tname).first()
        tracker_log=Tracker_logs.query.filter_by(Tracker_name=tname).all()
        time="0"
        for log in tracker_log:
            if log.Timestamp>time:
                time=log.Timestamp
        tracker.Last_Tracked=time
        db.session.commit()
        return redirect("/dashboard/{}".format(usern))

@app.route("/tracker/<usern>/<tname>/view",methods=["GET","POST"])
def view_tracker(usern,tname):
    if request.method=="GET":
        logs=Tracker_logs.query.filter_by(Tracker_name=tname).all()
        tracker=Trackers.query.filter_by(Name=tname).first()
        my_dpi=120
        fig=plt.figure(figsize=(1500/my_dpi, 500/my_dpi), dpi=my_dpi)        
        #fig.subplots_adjust(bottom=0.2)
        time=[]
        val=[]
        if tracker.TrackerType=="Numerical":
            for log in logs:
                time.append(log.Timestamp)
                val.append(int(log.Value))
        else:
             for log in logs:
                time.append(log.Timestamp)
                val.append((log.Value))
        plt.xlabel("TIME")
        plt.ylabel("VALUES")
        #plt.xticks(rotation=30, ha='right')
        plt.plot(time,val)
        plt.savefig('./static/plot.png',dpi=my_dpi)
        plt.close()
        return render_template("log_dashboard.html",user=usern,tracker_logs=logs,name=tname)        

@app.route("/log/<usern>/<time>/delete",methods=["GET","POST"])
def del_log(usern,time):
    if request.method=="GET":
        log=Tracker_logs.query.filter_by(Timestamp=time).first()
        name=log.Tracker_name
        db.session.delete(log)
        db.session.commit()
        tracker=Trackers.query.filter_by(Name=name).first()
        tracker_log=Tracker_logs.query.filter_by(Tracker_name=name).all()
        time="0"
        for log in tracker_log:
            if log.Timestamp>time:
                time=log.Timestamp
        tracker.Last_Tracked=time
        db.session.commit()
        return redirect("/tracker/{}/{}/view".format(usern,name))

@app.route("/log/<usern>/<time>/edit",methods=["GET","POST"])
def update_log(usern,time):
    if request.method=="GET":
        logs=Tracker_logs.query.filter_by(Timestamp=time).first()
        name=logs.Tracker_name
        trackers=Trackers.query.filter_by(Name=name).first()
        if trackers.TrackerType=="boolean":
           return render_template("edit_log_bool.html",user=usern,log=logs)   
        if trackers.TrackerType=="Multiple Choice":
           setting=trackers.Settings
           setting_list=list(setting.split(','))
           return render_template("edit_log_mcq.html",settings=setting_list,user=usern,log=logs) 
        if trackers.TrackerType=="Time":
            return render_template("edit_log_time.html",user=usern,log=logs)
        return render_template("edit_log_gen.html",user=usern,log=logs)
    if request.method=="POST":
        note=request.form["notes"]
        val=request.form["val"]
        tim=request.form["timestamp"]
        logss=Tracker_logs.query.filter_by(Timestamp=tim).first()
        if logss:
            return render_template("Logging_error.html")
        logs=Tracker_logs.query.filter_by(Timestamp=time).first() 
        name=logs.Tracker_name
        logs.Timestamp=tim
        logs.Value=val
        logs.Notes=note
        db.session.commit()
        tracker=Trackers.query.filter_by(Name=name).first()
        tracker_log=Tracker_logs.query.filter_by(Tracker_name=name).all()
        time="0"
        for log in tracker_log:
            if log.Timestamp>time:
                time=log.Timestamp
        tracker.Last_Tracked=time
        db.session.commit()
        return redirect("/tracker/{}/{}/view".format(usern,name))

if  __name__ == '__main__':
  # Run the Flask app
  app.run(
    host='0.0.0.0',
    debug=True,
    port=8080
  )




