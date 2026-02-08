from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# Many-to-many relationship table for jobs and tags
job_tags = Table(
    'job_tags',
    Base.metadata,
    Column('job_id', Integer, ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class Industry(Base):
    __tablename__ = 'industries'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey('industries.id'), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for parent-child hierarchy
    parent = relationship('Industry', remote_side=[id], backref='children')
    jobs = relationship('Job', back_populates='industry')

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # position/job_type/company/skill
    color = Column(String(20), default='#1890ff')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    jobs = relationship('Job', secondary=job_tags, back_populates='tags')

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    company_name = Column(String(200), nullable=False)
    industry_id = Column(Integer, ForeignKey('industries.id'), nullable=True)
    industry_name = Column(String(200), nullable=True)  # Denormalized for quick access
    
    # Contact information
    apply_email = Column(String(200), nullable=True)
    email_subject_template = Column(Text, nullable=True)
    email_body_template = Column(Text, nullable=True)
    
    # Job requirements (stored as JSON)
    requirements = Column(JSON, nullable=True)
    # Example structure:
    # {
    #   "education": "本科及以上",
    #   "experience": "应届生",
    #   "location": "北京",
    #   "skills": ["Python", "SQL"],
    #   "salary": "15k-25k"
    # }
    
    # Source information
    source_url = Column(String(500), nullable=True)
    source_type = Column(String(50), nullable=True)  # 公众号/官网/手动
    raw_content = Column(Text, nullable=True)  # Original text backup
    published_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(20), default='active')  # draft/active/expired
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    industry = relationship('Industry', back_populates='jobs')
    tags = relationship('Tag', secondary=job_tags, back_populates='jobs')
