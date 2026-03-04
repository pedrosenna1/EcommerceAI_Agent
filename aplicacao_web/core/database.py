from sqlalchemy import create_engine
from sqlalchemy.orm import Session,sessionmaker


engine = create_engine('sqlite:///data.db', echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
