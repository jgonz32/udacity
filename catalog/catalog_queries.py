'''
Created on Apr 17, 2015

@author: jgonz2
'''
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from db.catalog_database_setup import Base, Manufacturer, Model, Specifications, CatalogUser

# This class 
class CatalogQueries():
    ''' CatalogQueries class contains common queries used in the catalog application
    
        The class is initialied by passing the the URL where the Catalog database is created
        
     '''
    def __init__(self, database_url):
        '''
        Constructor  'sqlite:///db/phonecatalogwithuser.db'
        '''
        engine = create_engine(database_url)
        Base.metadata.bind = engine
        
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()
        # self.manufacturers=self.get_all_manufacturers()
        
    # return a list of all manufacturers
    def get_all_manufacturers(self):
        return self.session.query(Manufacturer).all()
    
    # return a list of all phone models
    def get_all_phone_models(self):
        return self.session.query(Model).all()
    
    # return a list of 5 latest phones added
    def get_recent_models_list(self):
        models = self.session.query(Model, Manufacturer).join(Manufacturer, Manufacturer.id == Model.manufacturer_id).order_by(desc(Model.id)).limit(5).all()
        
        recent_models_added_list = []
        for m in models:
            recent_model = (m[0].id,m[0].name, m[1].id, m[1].name)
            recent_models_added_list.append(recent_model)
        
        return recent_models_added_list
    
    # return a list of tuples with the manufactures, count of phones by manufacturers and phone models list by manufacturers
    def get_phone_models_count(self):
        manufacturers = self.get_all_manufacturers()
        manufacturers_list = []
        for m in manufacturers:
          models_count = self.session.query(Model).filter_by(manufacturer_id=m.id).count()    
          models_list = self.session.query(Model).filter_by(manufacturer_id=m.id).all()
          m_details = (m.id, m.name, models_count, models_list)
          manufacturers_list.append(m_details)
        
        return manufacturers_list
    
    # Add a user to the database if he/she doesn't exists
    def create_user(self, login_session):
        newUser = CatalogUser(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
        self.session.add(newUser)
        self.session.commit()
        user = self.session.query(CatalogUser).filter_by(email=login_session['email']).one()
        return user.id

    # return user info based on id
    def get_user_info(self, user_id):
        user = self.session.query(CatalogUser).filter_by(id=user_id).one()
        return user

    # returned user id based on email address provided. Returns None if email doesn't exists
    def get_user_id(self, email):
        try:
            user = self.session.query(CatalogUser).filter_by(email=email).one()
            return user.id
        except:
            return None
    
    # return manufacturer object based on manufacturer name
    def search_by_manufacturer_name(self, manufacturer):
        return self.session.query(Manufacturer).filter_by(name=manufacturer).one()
    
    # return model object based on model name
    def search_by_phone_model_name(self, model):
        return self.session.query(Model).filter_by(name=model).one()
    
    # return specifciation based on model id name
    def search_specifications_by_model_id(self, id):
        return self.session.query(Specifications).filter_by(model_id=id).one()

    # return manufacturer object based on manufacturer id
    def search_by_manufacturer_id(self, manufacturer_id):
        return self.session.query(Manufacturer).filter_by(id=manufacturer_id).one()

    # return model object based on model id
    def search_by_phone_model_id(self, model_id):
        return self.session.query(Model).filter_by(id=model_id).one()

    
