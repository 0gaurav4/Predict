import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import seaborn as sns
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.model_selection import train_test_split
from xgboost import plot_importance, plot_tree
from sklearn.metrics import mean_squared_error, mean_absolute_error
from timeseries import *
plt.style.use('fivethirtyeight')

def create_features(df, label=None):
    
    df['date'] = df.index
    df['hour'] = df['date'].dt.hour
    df['dayofweek'] = df['date'].dt.dayofweek
    df['quarter'] = df['date'].dt.quarter
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    df['dayofyear'] = df['date'].dt.dayofyear
    df['dayofmonth'] = df['date'].dt.day
    df['weekofyear'] = df['date'].dt.weekofyear
    
    X = df[['hour','dayofweek','quarter','month','year',
           'dayofyear','dayofmonth','weekofyear']]
    y = df[label]
    return X, y
    

def load_csv(filepath,col1,col2):
    df  = pd.read_csv(filepath,index_col=col1,parse_dates=[0])
    tdf = df[[col2]].copy()
    return tdf

def graph_one(tdf, y_col):
    color_pal = ["#F8766D", "#D39200", "#93AA00", "#00BA38", "#00C19F", "#00B9E3", "#619CFF", "#DB72FB"]
    title=f'{y_col} distribution over time'
    tdf.plot(style='.', figsize=(15,5), color=color_pal[0], title=title)
    plt.savefig(f'static/graphs/{title}.png',bbox_inches='tight')


def get_data(tdf,y_col):
    X,y = create_features(tdf,y_col)
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=.3,random_state=41)
    return X_train,X_test,y_train,y_test

def train(X_train,X_test,y_train,y_test):
    reg = xgb.XGBRegressor(n_estimators=1000)
    reg.fit(X_train, 
            y_train,
            eval_set=[(X_train, y_train), (X_test, y_test)],
            early_stopping_rounds=50,
            verbose=False)
    return reg

def plot_features_important(model,height=.9):
    plot_importance(model,height=height)
    title= "importance of features"
    plt.savefig(f'static/graphs/{title}.png',bbox_inches='tight')

def predictTimeseries(reg, tdf, y_col):
    X,y = create_features(tdf,y_col)
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=.3,shuffle=False)
    X_test['Prediction'] = reg.predict(X_test)
    X_test[y_col] = y_test
    X_train[y_col] = y_train
    X_all = pd.concat([X_test,X_train],sort=False)
    return X_all
   
    
