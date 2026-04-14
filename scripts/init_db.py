from app.db.session import engine, Base
from app.db.base import User, Circular, ApiKey # Import models to register them with Base

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

if __name__ == "__main__":
    init_db()
