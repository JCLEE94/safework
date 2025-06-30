"""
사용자 테이블 생성 마이그레이션
User table creation migration
"""

from sqlalchemy import text


async def create_users_table(db):
    """사용자 관련 테이블 생성"""
    
    # 1. users 테이블 생성
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(100) NOT NULL,
            department VARCHAR(100),
            role VARCHAR(50) NOT NULL DEFAULT 'user',
            
            -- Security fields
            is_active BOOLEAN DEFAULT TRUE,
            is_verified BOOLEAN DEFAULT FALSE,
            
            -- Timestamps
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE,
            password_changed_at TIMESTAMP WITH TIME ZONE,
            
            -- Additional security
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP WITH TIME ZONE,
            
            -- Profile
            phone VARCHAR(20),
            profile_image TEXT,
            
            -- Preferences
            language VARCHAR(10) DEFAULT 'ko',
            timezone VARCHAR(50) DEFAULT 'Asia/Seoul'
        )
    """))
    
    # 2. user_sessions 테이블 생성
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            refresh_token VARCHAR(255) UNIQUE,
            
            -- Session info
            ip_address VARCHAR(45),
            user_agent TEXT,
            device_info TEXT,
            
            -- Time info
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            
            -- Status
            is_active BOOLEAN DEFAULT TRUE,
            logout_at TIMESTAMP WITH TIME ZONE
        )
    """))
    
    # 3. user_login_history 테이블 생성
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS user_login_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            
            -- Login info
            login_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            logout_time TIMESTAMP WITH TIME ZONE,
            login_type VARCHAR(50) DEFAULT 'normal',
            
            -- Access info
            ip_address VARCHAR(45),
            user_agent TEXT,
            device_info TEXT,
            location VARCHAR(200),
            
            -- Result
            success BOOLEAN DEFAULT TRUE,
            failure_reason VARCHAR(200)
        )
    """))
    
    # 4. 인덱스 생성
    await db.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
    await db.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"))
    await db.execute(text("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)"))
    await db.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)"))
    await db.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)"))
    await db.execute(text("CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON user_login_history(user_id)"))
    await db.execute(text("CREATE INDEX IF NOT EXISTS idx_login_history_time ON user_login_history(login_time)"))
    
    # 5. 기본 관리자 계정 생성
    await db.execute(text("""
        INSERT INTO users (email, password_hash, name, role, is_active, is_verified, created_at)
        VALUES (
            'admin@safework.local',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeJLaKwnyU6t6V5rS',  -- 'admin123!'
            '시스템 관리자',
            'admin',
            TRUE,
            TRUE,
            NOW()
        )
        ON CONFLICT (email) DO NOTHING
    """))
    
    await db.commit()
    print("✅ 사용자 테이블 생성 완료")


async def drop_users_table(db):
    """사용자 관련 테이블 삭제 (롤백용)"""
    await db.execute(text("DROP TABLE IF EXISTS user_login_history CASCADE"))
    await db.execute(text("DROP TABLE IF EXISTS user_sessions CASCADE"))
    await db.execute(text("DROP TABLE IF EXISTS users CASCADE"))
    await db.commit()
    print("🗑️ 사용자 테이블 삭제 완료")