from __future__ import print_function
import datetime
from datetime import timedelta, datetime
import time
from pyexpat.errors import messages
from pprint import pprint
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
import time
import mysql.connector
import requests
from flask_bcrypt import Bcrypt

global high
global hval

high = ""
hval = 0

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)
app.config["SESSION_TYPE"] = "filesystem"

Session(app)
bcrypt = Bcrypt(app)

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    passwd='Pratheek09!',
    port='3306',
    database='carbonfootprint'
)

mycursor = mydb.cursor()

def insertNewAccount(id, firstname, lastname, email, password):
    insertQuery = ('INSERT INTO users (id, firstName, LastName, email, password) VALUES (%s, %s, %s, %s, %s)')
    mycursor.execute(insertQuery, (id, firstname, lastname, (email), password))
    mydb.commit()
    print('Success!')


def insertData(emission):
    idQuery = ("SELECT id FROM users WHERE email = (%s)")
    mycursor.execute(idQuery, (session['id'],))
    id = mycursor.fetchone()
    print(id)
    print(emission)
    print(time.time())
    ts = time.time()
    utc_time = datetime.fromtimestamp(ts, pytz.utc)

    pst_timezone = pytz.timezone('America/Los_Angeles')

    pst_time = utc_time.astimezone(pst_timezone)


    insertQuery = ('INSERT INTO data (id, emmission, date) VALUES (%s, %s, %s)')
    mycursor.execute(insertQuery, (id[0], emission, pst_time))
    mydb.commit()
    print('Success!')


def brevoPush():
    ts = time.time()
    utc_time = datetime.fromtimestamp(ts, pytz.utc)
    pst_timezone = pytz.timezone('America/Los_Angeles')
    pst_time = utc_time.astimezone(pst_timezone)
    currweektotal = 0
    week = ts - 604800
    currWeek = []
    prevWeek = []
    otherCurrWeek = []
    othertotal = 0

    # loop if <data is greater than (week)>:
    # currweektotal+=data.em

    query1 = ("SELECT id FROM users WHERE email = %s")
    mycursor.execute(query1, (session['id'],))
    result1 = mycursor.fetchone()

    query = ("SELECT emmission FROM data WHERE (date > %s) AND (id = %s)")
    mycursor.execute(query, (week, result1[0],))
    result = mycursor.fetchall()
    for result in result:
        currWeek.append(float(result[0]))
        if len(result) == 2:
            currWeek.append(float(result[1]))

    for emissions in currWeek:
        currweektotal += emissions

    utc_time = datetime.fromtimestamp(week, pytz.utc)

    pst_timezone = pytz.timezone('America/Los_Angeles')

    pst_time = utc_time.astimezone(pst_timezone)

    print(pst_time)

    prevweektotal = 1
    prevweek = ts - 1209600



    # loop if <(prevweek)<data<(week)>:
    # prevweektotal+=data.em
    query2 = ("SELECT emmission FROM data WHERE date > (%s) AND date < (%s) AND id = %s")
    mycursor.execute(query2, (prevweek, week, result1[0]))
    result2 = mycursor.fetchall()
    for result in result2:
        prevWeek.append(float(result[0]))
        if len(result) == 2:
            prevWeek.append(float(result[1]))

    for emissions in prevWeek:
        prevweektotal += emissions

    utc_time = datetime.fromtimestamp(prevweek, pytz.utc)

    pst_timezone = pytz.timezone('America/Los_Angeles')

    pst_time = utc_time.astimezone(pst_timezone)

    print(pst_time)

    # change=((currweektotal-prevweektotal)*100)/prevweektotal
    # FOCH= change
    temp_list = [week]
    query3 = ("SELECT emmission FROM data WHERE date > %s")
    mycursor.execute(query3, (week,))
    result3 = mycursor.fetchall()
    for result in result3:
        otherCurrWeek.append(result[0])
        if len(result) == 2:
            otherCurrWeek.append(result[1])

    for emission in otherCurrWeek:
        othertotal += float(emission)

    query4 = ("SELECT COUNT(id) FROM users")
    mycursor.execute(query4)
    result4 = mycursor.fetchone()

    othertotal = othertotal / result4[0]

    url = "https://api.brevo.com/v3/contacts/"+session['id']+"?identifierType=email_id"

    payload = { "attributes": {
            "CAFO": currweektotal,
            "AVFO": othertotal,
            "FOCH":((currweektotal-prevweektotal)*100)/prevweektotal,
            "ACC1": high,
            "ACC2": hval
        } }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
    "api-key":"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"
    }

    response = requests.put(url, json=payload, headers=headers)

    print(response.text)

    return 1;


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('landing.html')

@app.route('/renderSignup', methods=['GET', 'POST'])
def renderSignup():
    return render_template('signup.html')

@app.route('/renderLogin', methods=['GET', 'POST'])
def renderLogin():
    return render_template('login.html')

@app.route('/renderMoreFacts', methods=['GET','POST'])
def moreFacts():
    return render_template('moreFacts.html')

@app.route('/renderMoreFacts1', methods=['GET', 'POST'])
def moreFacts1():
    return render_template('moreFacts1.html')

@app.route('/renderQuiz', methods=['GET','POST'])
def quiz():
    if not session.get('id'):
        return redirect('/renderLogin')
    return render_template('quiz.html')

@app.route('/createAccount', methods=['GET', 'POST'])
def createAccount():
    firstName = str(request.form['firstname'])
    lastName = str(request.form['lastname'])
    email = str(request.form['email'])
    password = str(request.form['pwd'])
    repass = str(request.form['repwd'])


    if (firstName == '' or lastName == '' or email == '' or password == '' or repass == ''):
        return render_template('signup.html', message='Please fill out all of parts!', color='red')
    else:
        if (password != repass):
            return render_template('signup.html', message='Passwords do not match!', color='red')
        else:
            id = 0
            mycursor.execute("SELECT COUNT(id) FROM users WHERE id IS NOT NULL")
            result = mycursor.fetchone()
            count = result[0]
            if count == 0:
                id = id + 0
            else:
                id = count
            encryptedPassword = bcrypt.generate_password_hash(password).decode('utf-8')
            insertNewAccount(id, firstName, lastName, email, encryptedPassword)
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key[
                'api-key'] = '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'

            api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
            create_contact = sib_api_v3_sdk.CreateContact(email=email, list_ids=[2])

            try:
                api_response = api_instance.create_contact(create_contact)
                pprint(api_response)
            except ApiException as e:
                print("Exception when calling ContactsApi->create_contact: %s\n" % e)

            return render_template('login.html', message='Success! Log in here.', color='green')


@app.route('/logIntoAccount', methods=['GET', 'POST'])
def LogIntoAccount():
    email = str(request.form['email'])
    password = str(request.form['pwd'])

    if (email == '' or password == ''):
        return render_template('login.html', message='Please enter all of the details!', color='red')
    else:
        query = ('SELECT password FROM users WHERE email = (%s)')
        mycursor.execute(query, (email,))
        databasePWD = mycursor.fetchone()
        if (not databasePWD):
            return render_template('login.html', message='Email not found', color='red')
        if bcrypt.check_password_hash(databasePWD[0], password):
            session['id'] = email
            print(session['id'])
            return redirect('/accountDashboard')
        else:
            return render_template('login.html', message='Password is incorrect', color ='red')


@app.route('/accountDashboard', methods=['GET', 'POST'])
def accountDashboard():
    if not session.get("id"):
        return redirect('/renderLogin')
    else:
        emissions = []
        date = []
        index_query = ("SELECT id FROM users WHERE email = %s")
        mycursor.execute(index_query, (session["id"],))
        result1 = mycursor.fetchone()

        query = ("SELECT emmission, date FROM data WHERE id = %s")
        mycursor.execute(query, (result1[0],))
        result = mycursor.fetchall()
        print(result)
        for result in result:
            emissions.append(float(result[0]))
            date.append(result[1])
        print(emissions)
        print(date)
        return render_template('accountDashboard.html', emission=emissions, time=date)

@app.route('/renderQuiz', methods=['GET','POST'])
def todayData():
    if not session.get('id'):
        return redirect('/renderLogin')
    return render_template('quiz.html')

@app.route('/emissionCalc', methods=['GET', 'POST'])
def emissionCalc():
    global high
    global hval
    transport = request.form.get('transport')
    miles = str(request.form['miles'])
    home = request.form.get('home')
    food = request.form.get('food')
    waste = request.form.get('waste')
    miles = float(miles)
    sum = 0
    transport_emm = 0
    food_emm = 0
    trash = 0


    if transport == "select" or miles == "select" or home == "select" or food == "select" or waste == "select":
        return render_template('quiz.html', message="Choose an option for all questions", color="red")
    elif transport == "walking/biking":
        transport_emm = 0
    elif transport == "electric/hybrid car":
        transport_emm = 0.0002
    elif transport == "gas car":
        transport_emm = 0.0089
    elif transport == "bus":
        transport_emm = 0.00014
    elif transport == "train":
        transport_emm = 0.00014
    elif transport == "airplane":
        transport_emm = 0.002

    transport_emm *= float(miles);

    if home == "very":
        eff = 0.00096
    elif home == "somewhat":
        eff = 0.005955
    elif home == "nope":
        eff = 0.011

    if food == "every meal":
        food_emm = 1.3
    elif food == "one meal":
        food_emm = 1
    elif food == "no beef":
        food_emm = 0.79
    elif food == "veg":
        food_emm = 0.66
    elif food == "vegan":
        food_emm = 0.56

    if waste == "yes":
        trash = 0
    elif waste == "tries":
        trash = 0.01355
    elif waste == "no":
        trash = 0.015

    if transport_emm > eff and transport_emm > food_emm and transport_emm > trash:
        high = "daily commute"
        hval = transport_emm
    elif eff > transport_emm and eff > food_emm and eff > trash:
        high = "energy usage"
        hval = eff
    elif food_emm > transport_emm and food_emm > eff and food_emm > trash:
        high = "dietary lifestyle"
        hval = food_emm
    elif trash > transport_emm and trash > food_emm and trash > eff:
        high = "disposal practices"
        hval = trash

    sum = transport_emm + eff + food_emm + trash
    hval = (hval / sum) * 100
    print(sum)
    print(hval)
    insertData(sum)
    brevoPush()

    return redirect('/accountDashboard')

if __name__ == '__main__':
    app.run(debug=True)
