from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///shopify_data.db")
Base = declarative_base()
Session = sessionmaker(bind=engine)

class BrandData(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    data = Column(JSON)

Base.metadata.create_all(engine)

def save_to_db(url, data):
    session = Session()
    session.merge(BrandData(url=url, data=data))
    session.commit()
