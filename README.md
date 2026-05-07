# Career Compass AI

AI-based career guidance and learning resource recommendation web application.

## Stack
- Frontend: React.js + Vite
- Authentication: Firebase Authentication
- Backend: FastAPI
- Database: PostgreSQL
- AI: Rule-based recommendation first, AI chatbot later

## Project Flow
1. Landing page
2. Signup / Login / Continue with Google
3. Protected student dashboard
4. Student profile setup
5. Interest and skills selection
6. Career recommendation results
7. Career detail
8. Career roadmap
9. Skill gap analysis
10. Learning resources
11. AI chatbot
12. Saved careers
13. Admin dashboard and CRUD screens

## Run Frontend
```bash
cd frontend
npm install
npm run dev
```

## Run Backend
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Important
Create your Firebase project and replace frontend/src/firebase/firebase.js config values.
Create PostgreSQL database and update backend/.env.
