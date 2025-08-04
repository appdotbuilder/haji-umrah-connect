from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List
from enum import Enum
from decimal import Decimal


# Enums
class UserRole(str, Enum):
    SEEKER = "seeker"  # Pencari layanan
    PROVIDER = "provider"  # Penyedia layanan
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class ServiceType(str, Enum):
    BADAL_HAJI = "badal_haji"
    BADAL_UMRAH = "badal_umrah"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"


class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"


class BlogStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password_hash: str = Field(max_length=255)
    full_name: str = Field(max_length=200)
    phone: str = Field(max_length=20)
    role: UserRole = Field(default=UserRole.SEEKER)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    # Relationships
    provider_profile: Optional["ProviderProfile"] = Relationship(back_populates="user")
    bookings_as_seeker: List["Booking"] = Relationship(back_populates="seeker")
    messages_sent: List["ChatMessage"] = Relationship(
        back_populates="sender", sa_relationship_kwargs={"foreign_keys": "[ChatMessage.sender_id]"}
    )
    messages_received: List["ChatMessage"] = Relationship(
        back_populates="receiver", sa_relationship_kwargs={"foreign_keys": "[ChatMessage.receiver_id]"}
    )
    reviews_given: List["Review"] = Relationship(back_populates="reviewer")
    notifications: List["Notification"] = Relationship(back_populates="user")
    blog_posts: List["BlogPost"] = Relationship(back_populates="author")


class ProviderProfile(SQLModel, table=True):
    __tablename__ = "provider_profiles"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    business_name: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    address: str = Field(max_length=500)
    city: str = Field(max_length=100)
    province: str = Field(max_length=100)
    postal_code: str = Field(max_length=10)
    license_number: Optional[str] = Field(default=None, max_length=100)
    years_experience: int = Field(default=0)
    is_verified: bool = Field(default=False)
    is_available: bool = Field(default=True)
    average_rating: Decimal = Field(default=Decimal("0"), decimal_places=2, max_digits=3)
    total_reviews: int = Field(default=0)
    total_completed_services: int = Field(default=0)
    gallery_images: List[str] = Field(default=[], sa_column=Column(JSON))
    certificates: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="provider_profile")
    services: List["Service"] = Relationship(back_populates="provider")
    bookings: List["Booking"] = Relationship(back_populates="provider")


class Service(SQLModel, table=True):
    __tablename__ = "services"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="provider_profiles.id")
    title: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    service_type: ServiceType
    price: Decimal = Field(decimal_places=2, max_digits=12)
    duration_days: int = Field(default=40)  # Default 40 days for haji
    max_capacity: int = Field(default=1)
    includes: List[str] = Field(default=[], sa_column=Column(JSON))  # What's included in the service
    requirements: List[str] = Field(default=[], sa_column=Column(JSON))  # Requirements from the seeker
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    provider: ProviderProfile = Relationship(back_populates="services")
    bookings: List["Booking"] = Relationship(back_populates="service")


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    seeker_id: int = Field(foreign_key="users.id")
    provider_id: int = Field(foreign_key="provider_profiles.id")
    service_id: int = Field(foreign_key="services.id")
    booking_date: datetime = Field(default_factory=datetime.utcnow)
    service_start_date: datetime
    service_end_date: datetime
    total_amount: Decimal = Field(decimal_places=2, max_digits=12)
    status: BookingStatus = Field(default=BookingStatus.PENDING)
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    special_requests: Optional[str] = Field(default=None, max_length=1000)
    seeker_notes: Optional[str] = Field(default=None, max_length=1000)
    provider_notes: Optional[str] = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    seeker: User = Relationship(back_populates="bookings_as_seeker")
    provider: ProviderProfile = Relationship(back_populates="bookings")
    service: Service = Relationship(back_populates="bookings")
    review: Optional["Review"] = Relationship(back_populates="booking")


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="users.id")
    receiver_id: int = Field(foreign_key="users.id")
    booking_id: Optional[int] = Field(default=None, foreign_key="bookings.id")
    message: str = Field(max_length=2000)
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    sender: User = Relationship(
        back_populates="messages_sent", sa_relationship_kwargs={"foreign_keys": "[ChatMessage.sender_id]"}
    )
    receiver: User = Relationship(
        back_populates="messages_received", sa_relationship_kwargs={"foreign_keys": "[ChatMessage.receiver_id]"}
    )


class Review(SQLModel, table=True):
    __tablename__ = "reviews"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="bookings.id", unique=True)
    reviewer_id: int = Field(foreign_key="users.id")
    rating: int = Field(ge=1, le=5)  # 1-5 stars
    comment: Optional[str] = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    booking: Booking = Relationship(back_populates="review")
    reviewer: User = Relationship(back_populates="reviews_given")


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    status: NotificationStatus = Field(default=NotificationStatus.UNREAD)
    notification_type: str = Field(max_length=50)  # booking, message, review, etc.
    related_id: Optional[int] = Field(default=None)  # ID of related entity
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="notifications")


class BlogPost(SQLModel, table=True):
    __tablename__ = "blog_posts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="users.id")
    title: str = Field(max_length=300)
    slug: str = Field(unique=True, max_length=300)
    content: str
    excerpt: Optional[str] = Field(default=None, max_length=500)
    featured_image: Optional[str] = Field(default=None, max_length=500)
    status: BlogStatus = Field(default=BlogStatus.DRAFT)
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    view_count: int = Field(default=0)
    published_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    author: User = Relationship(back_populates="blog_posts")


class SystemSettings(SQLModel, table=True):
    __tablename__ = "system_settings"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, max_length=100)
    value: str = Field(max_length=2000)
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(max_length=200)
    phone: str = Field(max_length=20)
    role: UserRole = Field(default=UserRole.SEEKER)


class UserLogin(SQLModel, table=False):
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)


class UserUpdate(SQLModel, table=False):
    full_name: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class ProviderProfileCreate(SQLModel, table=False):
    business_name: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    address: str = Field(max_length=500)
    city: str = Field(max_length=100)
    province: str = Field(max_length=100)
    postal_code: str = Field(max_length=10)
    license_number: Optional[str] = Field(default=None, max_length=100)
    years_experience: int = Field(default=0)


class ProviderProfileUpdate(SQLModel, table=False):
    business_name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    address: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=100)
    province: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=10)
    license_number: Optional[str] = Field(default=None, max_length=100)
    years_experience: Optional[int] = Field(default=None)
    is_available: Optional[bool] = Field(default=None)
    gallery_images: Optional[List[str]] = Field(default=None)
    certificates: Optional[List[str]] = Field(default=None)


class ServiceCreate(SQLModel, table=False):
    title: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    service_type: ServiceType
    price: Decimal = Field(decimal_places=2, max_digits=12)
    duration_days: int = Field(default=40)
    max_capacity: int = Field(default=1)
    includes: List[str] = Field(default=[])
    requirements: List[str] = Field(default=[])


class ServiceUpdate(SQLModel, table=False):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    price: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=12)
    duration_days: Optional[int] = Field(default=None)
    max_capacity: Optional[int] = Field(default=None)
    includes: Optional[List[str]] = Field(default=None)
    requirements: Optional[List[str]] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class BookingCreate(SQLModel, table=False):
    service_id: int
    service_start_date: datetime
    special_requests: Optional[str] = Field(default=None, max_length=1000)


class BookingUpdate(SQLModel, table=False):
    status: Optional[BookingStatus] = Field(default=None)
    payment_status: Optional[PaymentStatus] = Field(default=None)
    seeker_notes: Optional[str] = Field(default=None, max_length=1000)
    provider_notes: Optional[str] = Field(default=None, max_length=1000)


class ChatMessageCreate(SQLModel, table=False):
    receiver_id: int
    booking_id: Optional[int] = Field(default=None)
    message: str = Field(max_length=2000)


class ReviewCreate(SQLModel, table=False):
    booking_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class ReviewUpdate(SQLModel, table=False):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class NotificationCreate(SQLModel, table=False):
    user_id: int
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    notification_type: str = Field(max_length=50)
    related_id: Optional[int] = Field(default=None)


class BlogPostCreate(SQLModel, table=False):
    title: str = Field(max_length=300)
    content: str
    excerpt: Optional[str] = Field(default=None, max_length=500)
    featured_image: Optional[str] = Field(default=None, max_length=500)
    tags: List[str] = Field(default=[])


class BlogPostUpdate(SQLModel, table=False):
    title: Optional[str] = Field(default=None, max_length=300)
    content: Optional[str] = Field(default=None)
    excerpt: Optional[str] = Field(default=None, max_length=500)
    featured_image: Optional[str] = Field(default=None, max_length=500)
    status: Optional[BlogStatus] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)


class SystemSettingsCreate(SQLModel, table=False):
    key: str = Field(max_length=100)
    value: str = Field(max_length=2000)
    description: Optional[str] = Field(default=None, max_length=500)


class SystemSettingsUpdate(SQLModel, table=False):
    value: str = Field(max_length=2000)
    description: Optional[str] = Field(default=None, max_length=500)
