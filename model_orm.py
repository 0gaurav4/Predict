
from datetime import datetime
from sqlalchemy import  create_engine
from sqlalchemy import Column,String,Integer,Float,ForeignKey,DateTime
from sqlalchemy.ext.declarative import declarative_base

Base= declarative_base()

#We will create out user table

class User(Base):
    __tablename__="users"
    id= Column(Integer, primary_key=True)
    username= Column(String(20), nullable=False)
    email=Column(String(40), unique=True, nullable=False)
    password=Column(String(15), unique=True, nullable=False)
    created_at=Column(DateTime,default=datetime.utcnow,nullable=False)

    def __rep__(self)->str:
        return f"{self.id}{self.username}|{self.name}{self.created_at}"

class DataSet(Base):
    __tablename__="dataset"
    id=Column(Integer, primary_key=True)
    filename=Column(String,nullable=False)
    filepath=Column(String, nullable=False)
    datatype=Column(String,nullable=False)
    user_id = Column(Integer,ForeignKey('users.id'))
    created_at=Column(DateTime,default=datetime.utcnow,nullable=False)

    def __rep__(self)->str:
        return f"{self.id}{self.filename}|{self.datatype}{self.created_at}"



if __name__== "__main__":
    engine=create_engine("sqlite:///model.sqlite")
    Base.metadata.create_all(engine)




    

