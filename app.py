import json
from werkzeug.utils import secure_filename
from model_orm import User
import os
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from flask import Flask,render_template, request, flash, redirect, session, url_for
import pandas as pd
import timeseries as ts
import plotly.graph_objects as go


from model_orm import DataSet

app = Flask(__name__)
app.secret_key = 'thisisaverysecretkey'

def opendb():
    engine = create_engine("sqlite:///model.sqlite")
    Session = sessionmaker(bind=engine)
    return Session()

@app.route('/', methods=['GET','POST'])
def login():
    # if session['isauth']:
    #     return redirect('/home')
    if request.method == 'POST':
        email = request.form.get('email')
        Password  = request.form.get('psw')
        print(email,Password)
        if not email or len(email) < 11:
            flash("❌ Enter correct email", 'danger')
            return redirect('/')
        elif not Password:
            flash('❌ Password is required', 'danger')
            return redirect('/')
        elif 'isauth' in session and session['isauth']:
            return redirect('/home')
        # more like this
        else:
            with opendb() as  db:
                query = db.query(User).filter(User.email == email).first()
                if query is not None and query.password == Password:        
                    session['isauth'] = True
                    session['id'] = True
                    session['name'] = True
                    flash('Login Successfull', 'success')
                    return redirect('/uploads')
                else:
                    flash('❌ There was an error while Logging in.','danger')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        email = request.form.get('email')
        username = request.form.get('username')
        confirm_password = request.form.get('confirm_password')
        password = request.form.get('password')
        if username and password and confirm_password and email:
            if confirm_password != password:
                flash('❌ Password do not match','danger')
                return redirect('/register')
            else:
                db =opendb()
                
                if db.query(User).filter(User.email==email).first() is not None:
                    flash('❌ Please use a different email address','danger')
                    db.close()
                    return redirect('/register')
                elif db.query(User).filter(User.username==username).first() is not None:
                    flash('❌ Please use a different username','danger')
                    db.close()
                    return redirect('/register')
                elif db.query(User).filter(User.password==password).first() is not None:
                    flash('❌ Please use a different password','danger')
                    db.close()
                    return redirect('/register')
                else:
                    user = User(username=username, email=email, password=password)  
                    db.add(user)
                    db.commit()
                    db.close()
                    flash('Congratulations, you are now a registered user!','success')
                    return redirect(url_for('login'))
        else:
            flash('❌ Fill all the fields','danger')
            return redirect('/register')

    return render_template('register.html', title='Sign Up page')

@app.route('/home')
def home():
    return render_template('home.html')

def allowed_files(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {"csv","xlsx","json"}

@app.route('/uploads', methods=['GET','POST'])
def uploadImage():
    if request.method == 'POST':
        print(request.files)
        if 'file' not in request.files:
            flash('❌ No file uploaded','danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('❌ no file selected','danger')
            return redirect(request.url)
        if file and allowed_files(file.filename):
            print(file.filename)
            db = opendb()
            filename = secure_filename(file.filename)
            path = os.path.join(os.getcwd(),"static/uploads", filename)
            print(path)
            file.save(path)
            upload = DataSet(filename=filename,filepath =f"/static/uploads/{filename}", datatype = os.path.splitext(file.filename)[1],user_id=session.get('id',1))
            db.add(upload)
            db.commit()
            flash('file uploaded and saved','success')
            session['uploaded_file'] = f"/static/uploads/{filename}"
            return redirect('/files')
        else:
            flash('❌ Wrong file selected, only csv, xlxs and json files allowed','danger')
            return redirect(request.url)
   
    return render_template('upload.html',title='upload file')


@app.route('/files')
def filelisting():
    db = opendb()
    filelist = db.query(DataSet).all()
    db.close()
    return render_template('files.html', filelist=filelist)

@app.route('/logout')
def logout():
    if "isauth" in session:
        session.pop('isauth')
    return redirect ("/")


@app.route('/path')
def path():
    return render_template('expression')

@app.route('/predict/<int:id>')
def predict(id):
    sess=opendb()
    data = sess.query(DataSet).filter(DataSet.id==id).first()
    sess.commit()
    df = pd.read_csv(data.filepath[1:])
    sess.close()
    columns = df.columns.tolist()
    
    return render_template('column_selector.html',data=data,df = df.head().to_html(),col1 = columns,col2=columns)

@app.route('/train',methods =['GET','POST'])
def train():
    if request.method == "POST":
        session['col1'] = request.form.get('col1')
        session['filepath'] = request.form.get('filepath')
        session['col2'] = request.form.get('col2')
        flash("columns selected",'success')
        
        return redirect('/train')
    graphs = {}
    if 'prediction_graph_1' in session:
        graphs['prediction_graph_1'] = session['prediction_graph_1']
    return render_template('train.html',graphs=graphs)
    
@app.route('/train_timeseries')
def train_timeseries():
    xc = request.args.get('x')
    yc = request.args.get('y')
    f = request.args.get('f')[1:]
    try:
        tdf = ts.load_csv(f,xc,yc)
        print('dataframe loaded')
        # print(tdf.head())
        X,y = ts.create_features(tdf,yc)
        # print(X.head(),y.head())
        X_train,X_test,y_train,y_test = ts.get_data(tdf,yc)
        model = ts.train(X_train,X_test,y_train,y_test)
        print('model trained')  
        out_df = ts.predictTimeseries(model,tdf,yc)
        print(out_df.columns.tolist())
        print(out_df.head())
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=out_df.index,y=out_df[yc],name='actual'))
        fig.add_trace(go.Scatter(x=out_df.index,y=out_df['Prediction'],name='prediction'))

        fig.update_layout(title_text=f'Prediction of {yc}',xaxis_title=f'Time',yaxis_title=f'{yc}')
        graph_file = f"static/graphs/{yc}_{xc}.html"
        fig.write_html(graph_file, include_plotlyjs='cdn',full_html=False)
        session['prediction_graph_1'] = graph_file
    except Exception as e:
        flash('Please select dataset file having Date-Time values.','danger')
        flash('❌There was an error to load graph','danger')
        
    return redirect('/train')

@app.route('/delete/<int:id>')
def delete(id):
    sess=opendb()
    try:
        sess.query(DataSet).filter(DataSet.id==id).delete()
        sess.commit()
        sess.close()
        return redirect('/files')
    except Exception as e:
        return f" ❌ There was a problem while deleting {e}"


if __name__ == '__main__':
  app.run(host='127.0.0.1', port=5000, debug=True)





 

