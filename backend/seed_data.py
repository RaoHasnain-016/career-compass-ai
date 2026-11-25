from app.database import SessionLocal
from app.models.career_model import Career
from app.models.roadmap_model import RoadmapStage
from app.models.resource_model import LearningResource


def add_career(db, data):
    existing = db.query(Career).filter(Career.title == data["title"]).first()

    if existing:
        return existing

    career = Career(**data)
    db.add(career)
    db.commit()
    db.refresh(career)
    return career


def add_roadmap_stage(db, career_id, stage_order, title, description, required_skills, suggested_resources):
    existing = (
        db.query(RoadmapStage)
        .filter(
            RoadmapStage.career_id == career_id,
            RoadmapStage.stage_order == stage_order,
        )
        .first()
    )

    if existing:
        return existing

    stage = RoadmapStage(
        career_id=career_id,
        stage_order=stage_order,
        title=title,
        description=description,
        required_skills=required_skills,
        suggested_resources=suggested_resources,
        status=True,
    )

    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage


def add_resource(db, data):
    existing = db.query(LearningResource).filter(
        LearningResource.title == data["title"],
        LearningResource.skill == data["skill"]
    ).first()

    if existing:
        return existing

    resource = LearningResource(**data)
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def seed_careers(db):
    software_engineer = add_career(db, {
        "title": "Software Engineer",
        "field": "Technology",
        "overview": "Software engineers design, develop, test, and maintain software applications, websites, mobile apps, and backend systems.",
        "required_education": "Intermediate with Computer Science or Mathematics, followed by BS Software Engineering, BS Computer Science, or related IT degree.",
        "required_skills": [
            "Programming",
            "Problem Solving",
            "Logic Building",
            "Database",
            "Web Development",
            "Communication"
        ],
        "required_subjects": [
            "Computer Science",
            "Mathematics"
        ],
        "related_interests": [
            "Technology",
            "Problem Solving",
            "Software",
            "Innovation"
        ],
        "minimum_marks": 60,
        "future_scope": "High demand in software companies, startups, freelancing, web development, mobile app development, AI, cloud computing, cybersecurity, and data engineering.",
        "difficulty_level": "Moderate",
        "status": True,
    })

    data_analyst = add_career(db, {
        "title": "Data Analyst",
        "field": "Data",
        "overview": "Data analysts collect, clean, analyze, and visualize data to help organizations make better decisions.",
        "required_education": "Bachelor degree in Computer Science, Statistics, Mathematics, Business Analytics, or related field.",
        "required_skills": [
            "Data Analysis",
            "Statistics",
            "Excel",
            "SQL",
            "Python",
            "Communication"
        ],
        "required_subjects": [
            "Mathematics",
            "Statistics",
            "Computer Science"
        ],
        "related_interests": [
            "Data",
            "Problem Solving",
            "Research",
            "Technology"
        ],
        "minimum_marks": 55,
        "future_scope": "Strong demand in IT companies, banks, e-commerce, healthcare, marketing, and business intelligence roles.",
        "difficulty_level": "Moderate",
        "status": True,
    })

    doctor = add_career(db, {
        "title": "Doctor",
        "field": "Medical",
        "overview": "Doctors diagnose, treat, and help prevent illnesses and injuries. They work in hospitals, clinics, and healthcare organizations.",
        "required_education": "Matric Science, FSc Pre-Medical, medical entry test, and MBBS or related medical degree.",
        "required_skills": [
            "Communication",
            "Research",
            "Helping People",
            "Critical Thinking",
            "Biology Knowledge"
        ],
        "required_subjects": [
            "Biology",
            "Chemistry",
            "Physics"
        ],
        "related_interests": [
            "Medical",
            "Helping People",
            "Science",
            "Research"
        ],
        "minimum_marks": 75,
        "future_scope": "Strong scope in hospitals, clinics, medical research, specialization, healthcare management, and public health.",
        "difficulty_level": "Difficult",
        "status": True,
    })

    business_analyst = add_career(db, {
        "title": "Business Analyst",
        "field": "Business",
        "overview": "Business analysts study business problems, analyze processes, and suggest improvements using data and communication skills.",
        "required_education": "Intermediate or Bachelor degree in Business, Commerce, IT, Economics, or related field.",
        "required_skills": [
            "Communication",
            "Analysis",
            "Problem Solving",
            "Management",
            "Excel"
        ],
        "required_subjects": [
            "Business Studies",
            "Mathematics",
            "Economics"
        ],
        "related_interests": [
            "Business",
            "Management",
            "Problem Solving",
            "Data"
        ],
        "minimum_marks": 50,
        "future_scope": "Good scope in companies, startups, banks, IT firms, consulting organizations, and project management roles.",
        "difficulty_level": "Moderate",
        "status": True,
    })

    graphic_designer = add_career(db, {
        "title": "Graphic Designer",
        "field": "Design",
        "overview": "Graphic designers create visual content for branding, social media, websites, marketing, and digital products.",
        "required_education": "Intermediate or Bachelor degree in Design, Fine Arts, Media Studies, Computer Arts, or self-learning with portfolio.",
        "required_skills": [
            "Creativity",
            "Design",
            "Communication",
            "UI Design",
            "Visual Thinking"
        ],
        "required_subjects": [
            "Arts",
            "Computer Science"
        ],
        "related_interests": [
            "Design",
            "Arts",
            "Creativity",
            "Technology"
        ],
        "minimum_marks": 45,
        "future_scope": "Good scope in freelancing, agencies, startups, UI/UX design, branding, advertising, and social media marketing.",
        "difficulty_level": "Moderate",
        "status": True,
    })

    teacher = add_career(db, {
        "title": "Teacher",
        "field": "Education",
        "overview": "Teachers guide students, explain concepts, prepare lessons, evaluate learning, and support academic growth.",
        "required_education": "Bachelor degree in relevant subject, B.Ed or teaching certification depending on institution requirements.",
        "required_skills": [
            "Communication",
            "Leadership",
            "Patience",
            "Subject Knowledge",
            "Presentation"
        ],
        "required_subjects": [
            "Education",
            "English",
            "Mathematics"
        ],
        "related_interests": [
            "Teaching",
            "Helping People",
            "Education",
            "Communication"
        ],
        "minimum_marks": 50,
        "future_scope": "Scope in schools, colleges, academies, online teaching, curriculum design, and educational technology.",
        "difficulty_level": "Moderate",
        "status": True,
    })

    careers = {
        "software_engineer": software_engineer,
        "data_analyst": data_analyst,
        "doctor": doctor,
        "business_analyst": business_analyst,
        "graphic_designer": graphic_designer,
        "teacher": teacher,
    }

    # Department coverage for the FYP catalogue. These are curated starter
    # records; administrators can refine country-specific entry requirements.
    additional_careers = [
        {
            "key": "cybersecurity_analyst", "title": "Cybersecurity Analyst", "field": "Technology",
            "overview": "Cybersecurity analysts protect systems, networks, and information by identifying risks and improving security controls.",
            "required_education": "Senior-secondary Mathematics or Computing followed by a degree, diploma, or verified technical pathway in computing or cybersecurity.",
            "required_skills": ["Programming", "Database", "Problem Solving", "Research", "Communication"],
            "required_subjects": ["Computer Science", "Mathematics"],
            "related_interests": ["Technology", "Problem Solving", "Research"], "minimum_marks": 60,
            "future_scope": "Roles in security operations, cloud security, incident response, and risk management.", "difficulty_level": "Difficult", "status": True,
        },
        {
            "key": "civil_engineer", "title": "Civil Engineer", "field": "Engineering",
            "overview": "Civil engineers plan and deliver infrastructure such as buildings, transport systems, water networks, and public works.",
            "required_education": "Senior-secondary Mathematics and Physics followed by an accredited civil engineering degree where required.",
            "required_skills": ["Mathematics", "Problem Solving", "Project Management", "Communication"],
            "required_subjects": ["Mathematics", "Physics"],
            "related_interests": ["Problem Solving", "Technology", "Management"], "minimum_marks": 60,
            "future_scope": "Infrastructure, construction, transport, environmental projects, and consulting.", "difficulty_level": "Difficult", "status": True,
        },
        {
            "key": "accountant", "title": "Accountant", "field": "Business",
            "overview": "Accountants prepare, review, and explain financial information to help individuals and organisations make responsible decisions.",
            "required_education": "Senior-secondary commerce, business, or mathematics followed by an accounting degree or professional qualification pathway.",
            "required_skills": ["Mathematics", "Excel", "Analysis", "Communication", "Critical Thinking"],
            "required_subjects": ["Accounting", "Business Studies", "Mathematics", "Economics"],
            "related_interests": ["Business", "Data", "Problem Solving"], "minimum_marks": 50,
            "future_scope": "Audit, taxation, financial reporting, corporate finance, and public accounting.", "difficulty_level": "Moderate", "status": True,
        },
        {
            "key": "pharmacist", "title": "Pharmacist", "field": "Medical",
            "overview": "Pharmacists support safe and effective medicine use, patient counselling, and healthcare teams.",
            "required_education": "Science pathway with Biology and Chemistry followed by the required pharmacy degree and local licensing process.",
            "required_skills": ["Communication", "Research", "Critical Thinking", "Helping People"],
            "required_subjects": ["Biology", "Chemistry"],
            "related_interests": ["Medical", "Helping People", "Science", "Research"], "minimum_marks": 65,
            "future_scope": "Community and hospital pharmacy, pharmaceutical industry, quality assurance, and research.", "difficulty_level": "Difficult", "status": True,
        },
        {
            "key": "psychologist", "title": "Psychologist", "field": "Social Sciences",
            "overview": "Psychologists study behaviour and wellbeing, using ethical assessment, communication, and evidence-based support.",
            "required_education": "A psychology degree followed by postgraduate study, supervised practice, and local licensing where required.",
            "required_skills": ["Communication", "Research", "Critical Thinking", "Helping People"],
            "required_subjects": ["Biology", "Statistics", "English"],
            "related_interests": ["Helping People", "Research", "Communication"], "minimum_marks": 55,
            "future_scope": "Mental-health services, organisational psychology, education, research, and community work.", "difficulty_level": "Difficult", "status": True,
        },
        {
            "key": "lawyer", "title": "Lawyer", "field": "Law",
            "overview": "Lawyers research legal issues, advise clients, prepare documents, and represent interests within legal and ethical frameworks.",
            "required_education": "Relevant law degree and jurisdiction-specific professional examinations or supervised training.",
            "required_skills": ["Communication", "Research", "Critical Thinking", "Presentation"],
            "required_subjects": ["English", "History", "Social Studies"],
            "related_interests": ["Research", "Communication", "Helping People"], "minimum_marks": 60,
            "future_scope": "Legal practice, corporate compliance, public service, policy, and legal research.", "difficulty_level": "Difficult", "status": True,
        },
        {
            "key": "architect", "title": "Architect", "field": "Architecture",
            "overview": "Architects design functional, safe, and sustainable buildings while balancing user needs, regulations, and visual quality.",
            "required_education": "Mathematics, design, and science preparation followed by an accredited architecture programme and local licensing where required.",
            "required_skills": ["Design", "Mathematics", "Creativity", "Project Management", "Communication"],
            "required_subjects": ["Mathematics", "Arts & Design", "Physics"],
            "related_interests": ["Design", "Creativity", "Problem Solving"], "minimum_marks": 55,
            "future_scope": "Architecture firms, urban design, construction, sustainability, and visualisation.", "difficulty_level": "Difficult", "status": True,
        },
        {
            "key": "journalist", "title": "Journalist", "field": "Media & Communication",
            "overview": "Journalists research, verify, and communicate public-interest stories across print, broadcast, and digital media.",
            "required_education": "A media, journalism, communications, or related degree is useful; a verified reporting portfolio is essential.",
            "required_skills": ["Communication", "Research", "Writing", "Critical Thinking", "Presentation"],
            "required_subjects": ["English", "History", "Geography"],
            "related_interests": ["Communication", "Research", "Creativity"], "minimum_marks": 50,
            "future_scope": "Digital journalism, editorial work, broadcast media, communications, and content strategy.", "difficulty_level": "Moderate", "status": True,
        },
        {
            "key": "environmental_scientist", "title": "Environmental Scientist", "field": "Science",
            "overview": "Environmental scientists investigate environmental problems and support evidence-based solutions for communities and organisations.",
            "required_education": "Science preparation followed by environmental science, ecology, chemistry, geography, or related study.",
            "required_skills": ["Research", "Data Analysis", "Critical Thinking", "Communication"],
            "required_subjects": ["Biology", "Chemistry", "Geography", "Mathematics"],
            "related_interests": ["Science", "Research", "Helping People"], "minimum_marks": 55,
            "future_scope": "Environmental monitoring, sustainability, conservation, policy, and consulting.", "difficulty_level": "Moderate", "status": True,
        },
        {
            "key": "it_support_technician", "title": "IT Support Technician", "field": "Technology",
            "overview": "IT support technicians install, maintain, and troubleshoot devices, networks, software, and user access.",
            "required_education": "Technical or vocational certificate, diploma, or supervised entry pathway in IT support, networking, or computing.",
            "required_skills": ["Computer Applications", "Problem Solving", "Communication", "Research"],
            "required_subjects": ["Computer Science", "Mathematics", "Communication"],
            "related_interests": ["Technology", "Problem Solving", "Helping People"], "minimum_marks": 45,
            "future_scope": "IT support, help desk, network operations, cloud support, and progression to systems administration.", "difficulty_level": "Moderate", "status": True,
        },
        {
            "key": "electrical_technician", "title": "Electrical Engineering Technician", "field": "Engineering",
            "overview": "Electrical engineering technicians support installation, testing, maintenance, and troubleshooting of electrical systems under relevant supervision.",
            "required_education": "Electrical diploma, DAE, vocational certificate, or a supervised technical training pathway.",
            "required_skills": ["Applied Mathematics", "Applied Physics", "Problem Solving", "Communication"],
            "required_subjects": ["Applied Mathematics", "Applied Physics", "Electrical Fundamentals"],
            "related_interests": ["Technology", "Problem Solving", "Management"], "minimum_marks": 45,
            "future_scope": "Electrical maintenance, industrial systems, energy, automation, and progression to engineering study.", "difficulty_level": "Moderate", "status": True,
        },
        {
            "key": "medical_lab_technician", "title": "Medical Laboratory Technician", "field": "Medical",
            "overview": "Medical laboratory technicians support safe specimen handling, testing, quality processes, and healthcare teams.",
            "required_education": "Recognised laboratory technology diploma, vocational training, or country-specific supervised pathway.",
            "required_skills": ["Research", "Critical Thinking", "Communication", "Project Work"],
            "required_subjects": ["Biology", "Chemistry", "Applied Physics"],
            "related_interests": ["Medical", "Science", "Helping People"], "minimum_marks": 50,
            "future_scope": "Diagnostic laboratories, hospitals, quality assurance, and progression to health-science qualifications.", "difficulty_level": "Moderate", "status": True,
        },
        {
            "key": "accounting_technician", "title": "Accounting Technician", "field": "Business",
            "overview": "Accounting technicians support bookkeeping, invoices, payroll, reconciliations, and financial records using recognised processes and software.",
            "required_education": "Business or accounting diploma, vocational certificate, or recognised entry-level professional pathway.",
            "required_skills": ["Applied Mathematics", "Computer Applications", "Communication", "Project Work"],
            "required_subjects": ["Mathematics", "Business Studies", "Accounting"],
            "related_interests": ["Business", "Data", "Problem Solving"], "minimum_marks": 45,
            "future_scope": "Accounts support, payroll, bookkeeping, finance operations, and progression to professional accounting qualifications.", "difficulty_level": "Moderate", "status": True,
        },
    ]

    for item in additional_careers:
        key = item.pop("key")
        careers[key] = add_career(db, item)

    return careers


def seed_roadmaps(db, careers):
    roadmap_data = {
        "software_engineer": [
            ("Build Academic Foundation", "Focus on Computer Science, Mathematics, and logical thinking. Build strong basic concepts.", ["Mathematics", "Problem Solving"], ["Khan Academy Mathematics", "CS50 Introduction to Computer Science"]),
            ("Learn Programming Basics", "Start with Python or JavaScript. Learn variables, loops, functions, arrays, objects, and basic logic.", ["Programming", "Logic Building"], ["freeCodeCamp", "Python for Beginners"]),
            ("Learn Web and Database Development", "Learn HTML, CSS, JavaScript, React, FastAPI, SQL, and PostgreSQL basics.", ["Web Development", "Database"], ["MDN Web Docs", "PostgreSQL Tutorial"]),
            ("Build Real Projects", "Create portfolio projects such as career apps, dashboards, CRUD systems, and API-connected apps.", ["Problem Solving", "Database", "Web Development"], ["GitHub Projects", "React Documentation"]),
            ("Internship and Career Growth", "Apply for internships, improve GitHub profile, learn teamwork, and prepare for interviews.", ["Communication", "Problem Solving"], ["LinkedIn Learning Articles", "Interview Preparation Resources"]),
        ],
        "data_analyst": [
            ("Strengthen Math and Statistics", "Learn basic statistics, averages, probability, charts, and data interpretation.", ["Statistics", "Mathematics"], ["Khan Academy Statistics"]),
            ("Learn Excel and SQL", "Practice spreadsheets, formulas, pivot tables, and database querying.", ["Excel", "SQL"], ["Excel Easy", "SQLBolt"]),
            ("Learn Python for Data", "Learn Python basics, pandas, NumPy, and data cleaning.", ["Python", "Data Analysis"], ["Kaggle Learn Python", "freeCodeCamp Data Analysis"]),
            ("Build Dashboards", "Create dashboards using Power BI, Tableau, or Python visualization libraries.", ["Data Analysis", "Communication"], ["Microsoft Learn Power BI"]),
            ("Portfolio and Internship", "Build portfolio projects using real datasets and apply for internships.", ["Communication", "Problem Solving"], ["Kaggle Datasets"]),
        ],
        "doctor": [
            ("Build Science Foundation", "Focus deeply on Biology, Chemistry, and Physics at school/intermediate level.", ["Biology Knowledge", "Research"], ["Khan Academy Biology", "Khan Academy Chemistry"]),
            ("Prepare for Entry Test", "Practice medical entry test concepts, MCQs, time management, and revision schedule.", ["Critical Thinking", "Research"], ["Medical Entry Test Practice"]),
            ("Medical Degree Stage", "Complete MBBS or related medical degree with strong practical learning.", ["Communication", "Helping People"], ["Medical Study Resources"]),
            ("Clinical Training", "Complete house job, clinical practice, and supervised patient-care training.", ["Communication", "Critical Thinking"], ["Clinical Skills Videos"]),
            ("Specialization and Growth", "Choose specialization based on interest such as surgery, medicine, pediatrics, or research.", ["Research", "Helping People"], ["Medical Journals", "Healthcare Courses"]),
        ],
        "business_analyst": [
            ("Learn Business Basics", "Understand business processes, economics, management, and market behavior.", ["Management", "Analysis"], ["Business Studies Resources"]),
            ("Learn Excel and Analysis", "Practice Excel, charts, reports, and business data analysis.", ["Excel", "Analysis"], ["Excel Easy", "Google Sheets Training"]),
            ("Learn Communication and Documentation", "Practice requirement writing, presentations, and stakeholder communication.", ["Communication", "Management"], ["Communication Skills Course"]),
            ("Build Case Studies", "Analyze real business problems and create solution documents.", ["Problem Solving", "Analysis"], ["Business Case Study Examples"]),
            ("Internship and Growth", "Apply for business, product, operations, or analyst internships.", ["Communication", "Management"], ["LinkedIn Career Resources"]),
        ],
        "graphic_designer": [
            ("Learn Design Principles", "Understand color, typography, spacing, composition, and visual hierarchy.", ["Design", "Creativity"], ["Canva Design School"]),
            ("Learn Design Tools", "Practice tools such as Figma, Canva, Adobe Illustrator, or Photoshop.", ["UI Design", "Visual Thinking"], ["Figma Learn", "Adobe Tutorials"]),
            ("Build Portfolio Designs", "Create logos, posters, app screens, social media posts, and branding samples.", ["Creativity", "Design"], ["Behance Inspiration"]),
            ("Learn UI/UX Basics", "Understand user interface design, wireframes, and user-friendly layouts.", ["UI Design", "Communication"], ["Figma UI Design Tutorials"]),
            ("Freelancing and Growth", "Create portfolio, publish work, and apply for freelance or agency projects.", ["Communication", "Design"], ["Upwork Guides", "Fiverr Learn"]),
        ],
        "teacher": [
            ("Strengthen Subject Knowledge", "Focus on the subject you want to teach and build strong explanations.", ["Subject Knowledge", "Presentation"], ["Khan Academy", "Subject Tutorials"]),
            ("Learn Teaching Methods", "Understand lesson planning, student engagement, and classroom management.", ["Leadership", "Patience"], ["Teaching Methodology Resources"]),
            ("Practice Communication", "Improve speaking, explanation, and presentation skills.", ["Communication", "Presentation"], ["Public Speaking Resources"]),
            ("Gain Teaching Experience", "Teach juniors, create online lessons, or assist teachers.", ["Leadership", "Communication"], ["Online Teaching Platforms"]),
            ("Professional Growth", "Pursue B.Ed, certifications, and specialization in educational technology.", ["Subject Knowledge", "Leadership"], ["Education Courses"]),
        ],
    }

    department_roadmaps = {
        "Technology": [
            ("Build technical foundations", "Strengthen computing, mathematics, logical reasoning, and safe digital practices.", ["Programming", "Problem Solving"], ["CS50", "Khan Academy Mathematics"]),
            ("Practise with guided projects", "Complete small practical projects and document what you learned, tested, and improved.", ["Programming", "Communication"], ["freeCodeCamp", "GitHub Skills"]),
            ("Prepare for a pathway", "Choose a degree, certification, or supervised entry pathway and build evidence of your skills.", ["Research", "Communication"], ["Career pathway research"]),
        ],
        "Engineering": [
            ("Strengthen science and mathematics", "Build confidence in mathematics, physics, measurement, and problem solving.", ["Mathematics", "Problem Solving"], ["Khan Academy Mathematics", "Physics learning resources"]),
            ("Explore engineering practice", "Learn how engineers use design constraints, safety, teamwork, and project planning.", ["Project Management", "Communication"], ["Engineering project examples"]),
            ("Plan accredited study", "Research local accredited programmes, admission requirements, and practical placements.", ["Research", "Communication"], ["University programme research"]),
        ],
        "Business": [
            ("Build commercial foundations", "Develop numeracy, communication, business awareness, and ethical decision making.", ["Mathematics", "Communication"], ["Excel Easy", "Business studies resources"]),
            ("Analyse real cases", "Practise spreadsheets, reports, budgets, and short case studies using reliable data.", ["Excel", "Analysis"], ["Google Sheets training", "Business case studies"]),
            ("Create work-ready evidence", "Build a portfolio of analysis, presentations, and team projects before applying for placements.", ["Presentation", "Communication"], ["LinkedIn career resources"]),
        ],
        "Medical": [
            ("Strengthen science foundations", "Prioritise biology, chemistry, communication, and evidence-based study habits.", ["Research", "Communication"], ["Khan Academy Biology", "Khan Academy Chemistry"]),
            ("Understand regulated pathways", "Research local admission, accreditation, licensing, and supervised-practice requirements.", ["Research", "Critical Thinking"], ["Official university and regulator websites"]),
            ("Build professional readiness", "Develop patient-centred communication, ethics, and relevant supervised experience.", ["Helping People", "Communication"], ["Healthcare careers guidance"]),
        ],
        "Social Sciences": [
            ("Develop evidence and communication", "Build writing, research methods, statistics, listening, and ethical reasoning skills.", ["Research", "Communication"], ["Research methods courses"]),
            ("Explore supervised practice", "Learn the difference between academic study, supervised practice, and regulated professional roles.", ["Critical Thinking", "Helping People"], ["Professional association guidance"]),
            ("Plan a specialisation", "Compare degree, postgraduate, and professional-registration pathways in your country.", ["Research", "Communication"], ["University programme research"]),
        ],
        "Law": [
            ("Strengthen legal reasoning", "Practise careful reading, clear writing, research, and evidence-based argument.", ["Research", "Communication"], ["Legal writing resources"]),
            ("Learn the legal pathway", "Review accredited law programmes, entry requirements, and local professional qualification routes.", ["Critical Thinking", "Presentation"], ["Official legal regulator websites"]),
            ("Build experience ethically", "Seek approved observation, debate, writing, or supervised legal-experience opportunities.", ["Communication", "Presentation"], ["Moot court and debate resources"]),
        ],
        "Architecture": [
            ("Build design and technical foundations", "Strengthen mathematics, visual design, spatial thinking, and physics.", ["Design", "Mathematics"], ["Architecture design resources"]),
            ("Create a design portfolio", "Develop sketches, models, and design-process documentation that shows iteration and reasoning.", ["Creativity", "Communication"], ["Portfolio guidance"]),
            ("Research accredited study", "Compare accredited programmes, portfolio requirements, and local professional-registration steps.", ["Research", "Project Management"], ["University programme research"]),
        ],
        "Media & Communication": [
            ("Build reporting and storytelling", "Practise clear writing, interviewing, research, source verification, and digital communication.", ["Communication", "Research"], ["Journalism learning resources"]),
            ("Publish a small portfolio", "Create ethical, well-sourced articles, reports, or multimedia work and document your process.", ["Writing", "Critical Thinking"], ["Portfolio guidance"]),
            ("Prepare for placements", "Research newsroom, communications, content, and public-interest media opportunities.", ["Presentation", "Communication"], ["Media careers guidance"]),
        ],
        "Science": [
            ("Strengthen scientific foundations", "Build biology, chemistry, mathematics, data literacy, and evidence-evaluation skills.", ["Research", "Mathematics"], ["Khan Academy science"]),
            ("Practise investigation", "Complete safe supervised investigations, data analysis, and scientific communication tasks.", ["Data Analysis", "Critical Thinking"], ["Open science learning resources"]),
            ("Plan field experience", "Compare degree pathways and opportunities for fieldwork, laboratories, sustainability, or research projects.", ["Research", "Communication"], ["University programme research"]),
        ],
    }

    for key, career in careers.items():
        if key not in roadmap_data and career.field in department_roadmaps:
            roadmap_data[key] = department_roadmaps[career.field]

    for key, stages in roadmap_data.items():
        career = careers[key]
        for index, stage in enumerate(stages, start=1):
            add_roadmap_stage(
                db=db,
                career_id=career.career_id,
                stage_order=index,
                title=stage[0],
                description=stage[1],
                required_skills=stage[2],
                suggested_resources=stage[3],
            )


def seed_resources(db):
    resources = [
        {
            "title": "freeCodeCamp JavaScript Algorithms and Data Structures",
            "platform": "freeCodeCamp",
            "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8/",
            "skill": "Programming",
            "career_field": "Technology",
            "difficulty": "Beginner",
            "resource_type": "Course",
            "description": "Free JavaScript programming course for beginners.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "HackerRank Problem Solving Practice",
            "platform": "HackerRank",
            "url": "https://www.hackerrank.com/domains/algorithms",
            "skill": "Problem Solving",
            "career_field": "Technology",
            "difficulty": "Beginner",
            "resource_type": "Practice",
            "description": "Practice programming and problem-solving questions.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "PostgreSQL Tutorial",
            "platform": "PostgreSQL Tutorial",
            "url": "https://www.postgresqltutorial.com/",
            "skill": "Database",
            "career_field": "Technology",
            "difficulty": "Beginner",
            "resource_type": "Website",
            "description": "Free PostgreSQL tutorials with practical examples.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "MDN Web Docs",
            "platform": "Mozilla",
            "url": "https://developer.mozilla.org/",
            "skill": "Web Development",
            "career_field": "Technology",
            "difficulty": "Beginner",
            "resource_type": "Documentation",
            "description": "Free documentation for HTML, CSS, JavaScript, and web development.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Kaggle Learn Python",
            "platform": "Kaggle",
            "url": "https://www.kaggle.com/learn/python",
            "skill": "Python",
            "career_field": "Data",
            "difficulty": "Beginner",
            "resource_type": "Course",
            "description": "Free Python course for data analysis beginners.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Kaggle Learn Intro to SQL",
            "platform": "Kaggle",
            "url": "https://www.kaggle.com/learn/intro-to-sql",
            "skill": "SQL",
            "career_field": "Data",
            "difficulty": "Beginner",
            "resource_type": "Course",
            "description": "Free SQL basics for data analysis.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Khan Academy Statistics",
            "platform": "Khan Academy",
            "url": "https://www.khanacademy.org/math/statistics-probability",
            "skill": "Statistics",
            "career_field": "Data",
            "difficulty": "Beginner",
            "resource_type": "Course",
            "description": "Free statistics and probability lessons.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Khan Academy Biology",
            "platform": "Khan Academy",
            "url": "https://www.khanacademy.org/science/biology",
            "skill": "Biology Knowledge",
            "career_field": "Medical",
            "difficulty": "Beginner",
            "resource_type": "Course",
            "description": "Free biology lessons and practice.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Khan Academy Chemistry",
            "platform": "Khan Academy",
            "url": "https://www.khanacademy.org/science/chemistry",
            "skill": "Research",
            "career_field": "Medical",
            "difficulty": "Beginner",
            "resource_type": "Course",
            "description": "Free chemistry learning resources.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Communication Skills Course",
            "platform": "Coursera",
            "url": "https://www.coursera.org/courses?query=communication%20skills",
            "skill": "Communication",
            "career_field": "Business",
            "difficulty": "Beginner",
            "resource_type": "Course",
            "description": "Free-to-audit communication skills courses.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Excel Easy",
            "platform": "Excel Easy",
            "url": "https://www.excel-easy.com/",
            "skill": "Excel",
            "career_field": "Business",
            "difficulty": "Beginner",
            "resource_type": "Website",
            "description": "Free Excel tutorials for business and data analysis.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Canva Design School",
            "platform": "Canva",
            "url": "https://www.canva.com/designschool/",
            "skill": "Design",
            "career_field": "Design",
            "difficulty": "Beginner",
            "resource_type": "Course",
            "description": "Free design lessons and tutorials.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Figma Learn",
            "platform": "Figma",
            "url": "https://help.figma.com/hc/en-us/categories/360002042553-Learn-design",
            "skill": "UI Design",
            "career_field": "Design",
            "difficulty": "Beginner",
            "resource_type": "Documentation",
            "description": "Free Figma and UI design learning resources.",
            "is_free": True,
            "status": True,
        },
        {
            "title": "Public Speaking Resources",
            "platform": "Toastmasters",
            "url": "https://www.toastmasters.org/resources",
            "skill": "Presentation",
            "career_field": "Education",
            "difficulty": "Beginner",
            "resource_type": "Articles",
            "description": "Resources for improving speaking and presentation skills.",
            "is_free": True,
            "status": True,
        },
    ]

    for item in resources:
        add_resource(db, item)


def main():
    db = SessionLocal()

    try:
        print("Seeding careers...")
        careers = seed_careers(db)

        print("Seeding roadmaps...")
        seed_roadmaps(db, careers)

        print("Seeding learning resources...")
        seed_resources(db)

        print("Seed data inserted successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
