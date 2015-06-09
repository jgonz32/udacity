import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class CatalogUser(Base):
	__tablename__='cataloguser'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	email = Column(String(250), nullable=False)
	picture = Column(String(250), nullable=False)

class Manufacturer(Base):
	__tablename__='manufacturer'
	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False)
	user_id=Column(Integer, ForeignKey('cataloguser.id'))
	user = relationship(CatalogUser)

	@property
	def serialize(self):
		"""Return object data in easily serializeable format"""
		return {
		    'name'         : self.name,
		    'id'         : self.id,
		
		}

class Model(Base):
	__tablename__='model'
	name = Column(String(80), nullable=False)
	id = Column(Integer, primary_key=True)
	#img_url=Column(String(150), nullable=False)
	#date_added=Column(Date, nullable=False)
	manufacturer_id= Column(Integer, ForeignKey('manufacturer.id'))
	manufacturer = relationship(Manufacturer)
	user_id=Column(Integer, ForeignKey('cataloguser.id'))
	user = relationship(CatalogUser)
	
	@property
	def serialize(self):
	   """Return object data in easily serializeable format"""
	   return {
	       'name'         : self.name,
	       'id'         : self.id,
		   'manufacturer' : self.manufacturer.serialize
	   }

class Specifications(Base):
	__tablename__='specifications'
	id = Column(Integer, primary_key=True)
	size= Column(String(100))
	weight= Column(String(100))
	camera = Column(String(100))
	memory = Column(String(100))
	os= Column(String(100))
	display=Column(String(100))
	model_id=Column(Integer, ForeignKey('model.id'))
	model = relationship(Model)
	user_id=Column(Integer, ForeignKey('cataloguser.id'))
	user = relationship(CatalogUser)
	

	@property
	def serialize(self):
       
		return {
			'name'         : self.name,
			'size'         : self.size,
			'id'         : self.id,
			'weight'         : self.weight,
			'camera'         : self.camera,
			'os'         : self.price,
			'display'         : self.display,
			'memory'         : self.memory
		}


engine = create_engine('postgresql://catalog:b#stCatal0g@/phonecatalog')

Base.metadata.create_all(engine)
