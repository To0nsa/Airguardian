from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Create a base class for all ORM models using SQLAlchemy's declarative system.
# 
# `declarative_base()` returns a base class that maintains a catalog of classes
# and tables relative to it. All ORM models in the project should inherit from `Base`
# to be properly registered with SQLAlchemy’s metadata. This metadata is essential
# for generating database tables and handling ORM relationships.
#
# For example:
#     class MyModel(Base):
#         __tablename__ = 'my_table'
#         id = Column(Integer, primary_key=True)
#
# In this project, `Base` is used in `models.py` to define `Drone`, `Owner`, etc.,
# and later referenced by Alembic (see `env.py`) to autogenerate migrations.
