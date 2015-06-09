
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from catalog_database_setup import Manufacturer, Base, Model,Specifications,CatalogUser

engine = create_engine('postgresql+psycopg2://catalog:b#stCatal0g@/phonecatalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
session = DBSession()

user1= CatalogUser(name="Jorge G.", email="jorgeagd81@gmail.com", picture="picture")
user2= CatalogUser(name="Alejandro G.", email="alemgm2013@gmail.com", picture="picture")

manufacturer1 = Manufacturer(name = "HTC", user=user1)
session.add(manufacturer1)
session.commit()
manufacturer1 = Manufacturer(name = "Nokia", user=user1)
session.add(manufacturer1)
session.commit()
manufacturer1 = Manufacturer(name = "LG", user=user1)
session.add(manufacturer1)
session.commit()
manufacturer1 = Manufacturer(name = "Sony", user=user1)
session.add(manufacturer1)
session.commit()
manufacturer1 = Manufacturer(name = "Motorola", user=user1)
session.add(manufacturer1)
session.commit()

#Manufacturer - Apple
manufacturer1 = Manufacturer(name = "Apple", user=user1)

session.add(manufacturer1)
session.commit()

#model iPhone 5s
model1 = Model(name = "iPhone 5s",manufacturer = manufacturer1, user=user2)

session.add(model1)
session.commit()

specification1=Specifications(size="4.87 x 2.31 x 0.30 inches", weight="3.95 ounces", camera="8 Megapixel iSight camera with True Tone flash", memory="1 GB RAM DDR3", os="iOS 7", display="4.0 inches",model=model1, user=user2)

session.add(specification1)
session.commit()

#model iPhone 6
model2 = Model(name = "iPhone 6",manufacturer = manufacturer1, user=user1)

session.add(model2)
session.commit()

specification2=Specifications(size="5.44 x 2.64 x 0.27 inches", weight="4.55 ounces", camera="8-megapixel iSight camera with True Tone flash", memory="1 GB RAM", os="iOS 8", display="4.7 inches",model=model2, user=user1)

session.add(specification2)
session.commit()

#model iphone 6 plus
model3 = Model(name = "iPhone 6 plus",manufacturer = manufacturer1, user=user1)

session.add(model3)
session.commit()

specification3=Specifications(size="6.22 x 3.06 x 0.28 inches", weight="6.07 ounces", camera="8 MP, 3264 x 2448 pixels, optical image stabilization", memory="1 GB RAM", os="iOS 8", display="5.5 inches",model=model3, user=user1)

session.add(specification3)
session.commit()

#######################################################################################################################################################################################################################

#Manufacturer - Samsung
manufacturer2 = Manufacturer(name = "Samsung", user=user1)

session.add(manufacturer1)
session.commit()

#model Galaxy S6
model1 = Model(name = "Galaxy S6",manufacturer = manufacturer2, user=user1)

session.add(model1)
session.commit()

specification1=Specifications(size="5.64 x 2.77 x 0.27 inches", weight="4.87 ounces", camera="16MP Auto HDR Camera", memory="3 GB", os="Android 5.0", display="5.1 inches",model=model1, user=user1)

session.add(specification1)
session.commit()

#model Galaxy S6 Edge
model2 = Model(name = "Galaxy S6 Edge",manufacturer = manufacturer2, user=user1)

session.add(model2)
session.commit()

specification2=Specifications(size="5.44 x 2.64 x 0.27 inches", weight="4.55 ounces", camera="8-megapixel iSight camera with True Tone flash", memory="1 GB RAM", os="Android 5.0", display="4.7 inches",model=model2, user=user1)

session.add(specification2)
session.commit()

#model Galaxy Note 4
model3 = Model(name = "Galaxy Note 4",manufacturer = manufacturer2, user=user1)

session.add(model3)
session.commit() 

specification3=Specifications(size="6.04 inches x 3.09 inches x 0.33 inches", weight="6.21 oz", camera="16MP", memory="3GB", os="Android 4.4", display="5.7 Quad HD Super AMOLED, 2560 x 144",model=model3, user=user1)

session.add(specification3)
session.commit()
#########################################################################################################################################################################################################################



print "added phone models and specifications!"
