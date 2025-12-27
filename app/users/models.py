import enum
from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET
from app.database import Base

class Gender(enum.Enum):
    male = "male"
    female = "female"

class SubscriptionLevel(enum.Enum):
    base = "base"
    advanced = "advanced"

class Role(enum.Enum):
    user = "user"
    psycologist = "psychologist"

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, nullable=False)
    last_login_at = Column(DateTime(timezone=True))
    current_refresh_jti = Column(String, unique=True, index=True, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_ip = Column(INET, nullable=True)

    profile = relationship("Profiles", back_populates="user", uselist=False)

class Profiles(Base):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    fullname = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True, server_default=None)
    birthdate = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=True, server_default=None)
    country = Column(String, nullable=True, server_default=None)
    city = Column(String, nullable=True, server_default=None)
    subscription_level = Column(Enum(SubscriptionLevel), default=SubscriptionLevel.base, server_default="base", nullable=False)
    role = Column(Enum(Role), default=Role.user, server_default="user", nullable=False)
    imgSrc = Column(String, server_default=None, nullable=True)

    user = relationship("Users", back_populates="profile")