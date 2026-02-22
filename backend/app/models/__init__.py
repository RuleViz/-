from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text, Table, Float
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
    cart_items = relationship('CartItem', back_populates='job', cascade='all, delete-orphan')
    deliveries = relationship('Delivery', back_populates='job', cascade='all, delete-orphan')


class CartItem(Base):
    """购物车项目 - 用户收藏的待投递职位"""
    __tablename__ = 'cart_items'
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(100), nullable=False, default='default_user')  # 后续支持多用户
    
    # 投递配置（用户针对该职位的个性化设置）
    email_subject = Column(String(500), nullable=True)  # 自定义邮件主题
    cover_letter_style = Column(String(50), default='concise')  # concise/warm/technical
    include_resume = Column(Boolean, default=True)
    include_portfolio = Column(Boolean, default=False)
    include_video = Column(Boolean, default=False)
    
    # 状态
    status = Column(String(20), default='active')  # active/removed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship('Job', back_populates='cart_items')


class Delivery(Base):
    """投递记录 - 记录每次投递的详细信息"""
    __tablename__ = 'deliveries'
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(100), nullable=False, default='default_user')
    
    # 投递内容
    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)  # [{"name": "简历.pdf", "url": "..."}]
    
    # 投递状态
    status = Column(String(50), default='pending')  # pending/sent/delivered/viewed/replied/interview/rejected
    
    # 时间追踪
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    
    # 邮件追踪（如果邮件服务支持）
    message_id = Column(String(200), nullable=True)  # 邮件服务商返回的ID
    tracking_info = Column(JSON, nullable=True)  # 其他追踪信息
    
    # 面试记录
    interview_stage = Column(String(50), nullable=True)  # 一面/二面/HR面/offer
    interview_notes = Column(Text, nullable=True)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship('Job', back_populates='deliveries')


class JobLibrary(Base):
    """职位库 - 用户可以创建或加入的职位集合"""
    __tablename__ = 'job_libraries'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    author_id = Column(String(100), nullable=False, default='default_user')
    author_name = Column(String(100), nullable=False)
    author_type = Column(String(50), default='个人')  # 个人/高校认证/社群认证/博主认证
    
    # 外观
    cover_gradient = Column(String(200), default='linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
    cover_emoji = Column(String(10), default='💼')
    
    # 权限
    is_public = Column(Boolean, default=True)  # 公开/私有
    price_type = Column(String(20), default='free')  # free/paid/private
    price = Column(String(50), default='免费')
    
    # 统计
    job_count = Column(Integer, default=0)
    member_count = Column(Integer, default=0)
    
    # 状态
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jobs = relationship('JobLibraryItem', back_populates='library', cascade='all, delete-orphan')
    members = relationship('LibraryMember', back_populates='library', cascade='all, delete-orphan')


class JobLibraryItem(Base):
    """职位库中的职位关联"""
    __tablename__ = 'job_library_items'
    
    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey('job_libraries.id', ondelete='CASCADE'), nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    added_by = Column(String(100), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    library = relationship('JobLibrary', back_populates='jobs')
    job = relationship('Job')


class LibraryMember(Base):
    """职位库成员"""
    __tablename__ = 'library_members'
    
    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey('job_libraries.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(100), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    library = relationship('JobLibrary', back_populates='members')


class Resume(Base):
    __tablename__ = 'resumes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, default='default_user', index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(1024), nullable=False)
    status = Column(String(32), nullable=False, default='uploaded')
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parses = relationship('ResumeParse', back_populates='resume', cascade='all, delete-orphan')
    matches = relationship('MatchResult', back_populates='resume', cascade='all, delete-orphan')


class ResumeParse(Base):
    __tablename__ = 'resume_parses'

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, index=True)
    parsed_json = Column(JSON, nullable=True)
    extracted_fields = Column(JSON, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    parsed_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship('Resume', back_populates='parses')


class MatchResult(Base):
    __tablename__ = 'match_results'

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    score = Column(Float, nullable=False)
    reason_snippet = Column(Text, nullable=True)
    highlights = Column(JSON, nullable=True)
    template_recommendation = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship('Resume', back_populates='matches')
    job = relationship('Job')


class DeliveryJob(Base):
    __tablename__ = 'delivery_jobs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, default='default_user', index=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='SET NULL'), nullable=True, index=True)
    job_ids = Column(JSON, nullable=False, default=list)
    config = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default='created')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    logs = relationship('DeliveryLog', back_populates='delivery_job', cascade='all, delete-orphan')
    resume = relationship('Resume')


class DeliveryLog(Base):
    __tablename__ = 'delivery_logs'

    id = Column(Integer, primary_key=True, index=True)
    delivery_job_id = Column(Integer, ForeignKey('delivery_jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='SET NULL'), nullable=True, index=True)
    simulated_status = Column(String(50), nullable=False, default='queued', index=True)
    note = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    template_name = Column(String(100), nullable=True)
    attachment_names = Column(JSON, nullable=True)
    failure_reason = Column(Text, nullable=True)

    delivery_job = relationship('DeliveryJob', back_populates='logs')
    job = relationship('Job')
    resume = relationship('Resume')
