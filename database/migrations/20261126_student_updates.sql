BEGIN;

CREATE TABLE IF NOT EXISTS student_updates (
  update_id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  category VARCHAR(24) NOT NULL,
  title VARCHAR(180) NOT NULL,
  summary TEXT NOT NULL,
  url VARCHAR(120) NOT NULL,
  published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_student_updates_user_date ON student_updates (user_id, published_at);

CREATE TABLE IF NOT EXISTS student_update_reads (
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  notification_id VARCHAR(120) NOT NULL,
  read_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, notification_id)
);

COMMIT;
