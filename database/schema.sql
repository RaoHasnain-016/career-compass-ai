CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  firebase_uid VARCHAR(150) UNIQUE NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  role VARCHAR(30) NOT NULL DEFAULT 'Student',
  status VARCHAR(30) DEFAULT 'active',
  photo_url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student_profiles (
  profile_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID UNIQUE REFERENCES users(user_id),
  academic_level VARCHAR(50) NOT NULL,
  class_degree VARCHAR(100),
  marks_cgpa NUMERIC(5,2),
  favorite_subjects TEXT[],
  weak_subjects TEXT[],
  interests TEXT[],
  skills TEXT[],
  study_preference TEXT
);

CREATE TABLE careers (
  career_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(150) NOT NULL,
  field VARCHAR(100) NOT NULL,
  overview TEXT NOT NULL,
  required_education TEXT NOT NULL,
  required_skills TEXT[] NOT NULL,
  required_subjects TEXT[],
  related_interests TEXT[],
  future_scope TEXT,
  difficulty_level VARCHAR(50),
  status BOOLEAN DEFAULT TRUE
);

CREATE TABLE recommendations (
  recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(user_id),
  career_id UUID REFERENCES careers(career_id),
  match_score NUMERIC(5,2) NOT NULL,
  explanation TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roadmap_stages (
  stage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  career_id UUID REFERENCES careers(career_id),
  stage_order INT NOT NULL,
  title VARCHAR(150) NOT NULL,
  description TEXT NOT NULL,
  required_skills TEXT[],
  suggested_resources TEXT[]
);

CREATE TABLE learning_resources (
  resource_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(150) NOT NULL,
  platform VARCHAR(100) NOT NULL,
  url TEXT NOT NULL,
  skill VARCHAR(100) NOT NULL,
  career_field VARCHAR(100),
  difficulty VARCHAR(50),
  resource_type VARCHAR(50),
  is_free BOOLEAN DEFAULT TRUE,
  status BOOLEAN DEFAULT TRUE
);

CREATE TABLE saved_careers (
  saved_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(user_id),
  career_id UUID REFERENCES careers(career_id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT unique_user_career UNIQUE(user_id, career_id)
);

CREATE TABLE chat_messages (
  message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(user_id),
  question TEXT NOT NULL,
  response TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);
CREATE INDEX idx_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_resources_skill ON learning_resources(skill);
CREATE INDEX idx_saved_user_id ON saved_careers(user_id);
