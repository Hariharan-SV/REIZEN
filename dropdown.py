from flask import Flask,render_template,request
app=Flask(__name__)
app.static_folder='static'

@app.route('/auth',methods=['POST'])
def drop():
    if(request.method=='POST'):
        form=request.form
        s=form['station']
    return render_template('my_choice.html',name=s)

@app.route('/')
def view():
    return render_template('drop down.html')

if __name__ == '__main__':
   app.run(debug = True,port=5000)