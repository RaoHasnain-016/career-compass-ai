BEGIN;

CREATE TABLE IF NOT EXISTS recommendation_feedback (
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  career_id UUID NOT NULL REFERENCES careers(career_id) ON DELETE CASCADE,
  feedback VARCHAR(20) NOT NULL,
  PRIMARY KEY (user_id, career_id),
  CONSTRAINT ck_recommendation_feedback_value CHECK (feedback IN ('helpful', 'less_relevant'))
);

COMMIT;
