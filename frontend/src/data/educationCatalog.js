const sharedSubjects = [
  "English", "Mathematics", "Biology", "Chemistry", "Physics",
  "Computer Science", "Economics", "Business Studies", "Statistics",
  "History", "Geography", "Arts & Design",
];

export const countryOptions = [
  "Pakistan", "United States", "United Kingdom", "Canada", "Australia", "India", "Other",
];

const catalogs = {
  Pakistan: {
    levels: ["Matric", "Intermediate", "Diploma / DAE", "Technical / Vocational Certificate", "Bachelor", "Master", "Other"],
    streams: {
      Matric: ["Science", "Computer Science", "Arts & Humanities", "Commerce"],
      Intermediate: ["Pre-Medical", "Pre-Engineering", "ICS", "ICom", "FA / Humanities"],
      Bachelor: ["Computing & Technology", "Health Sciences", "Engineering", "Business & Management", "Social Sciences", "Arts & Design"],
      "Diploma / DAE": ["Civil Technology", "Electrical Technology", "Mechanical Technology", "Computer / IT Technology", "Electronics Technology", "Architecture Technology"],
      "Technical / Vocational Certificate": ["IT Support", "Web & Software", "Electrical", "Mechanical", "Construction", "Healthcare Support", "Business Administration"],
    },
    subjects: sharedSubjects,
  },
  "United States": {
    levels: ["Middle / High School", "High School Senior", "Diploma / Technical", "Undergraduate", "Graduate", "Other"],
    streams: { "Middle / High School": ["STEM", "Humanities", "Business", "Arts"], "High School Senior": ["AP / Honors STEM", "AP / Honors Humanities", "Career & Technical Education", "General"], Undergraduate: ["Major / Concentration", "Undeclared / Exploring"] },
    subjects: sharedSubjects,
  },
  "United Kingdom": {
    levels: ["Secondary / GCSE", "Sixth Form / A Level", "Diploma / Technical", "Undergraduate", "Postgraduate", "Other"],
    streams: { "Secondary / GCSE": ["STEM", "Humanities", "Arts", "Business"], "Sixth Form / A Level": ["Science", "Mathematics & Computing", "Humanities", "Business & Economics", "Creative Arts"], Undergraduate: ["Degree programme", "Exploring options"] },
    subjects: sharedSubjects,
  },
  Canada: {
    levels: ["Secondary School", "Senior Secondary", "Diploma / Technical", "Undergraduate", "Graduate", "Other"],
    streams: { "Secondary School": ["STEM", "Humanities", "Business", "Arts"], "Senior Secondary": ["University preparation", "College preparation", "Skilled trades", "General"], Undergraduate: ["Major / Concentration", "Exploring options"] },
    subjects: sharedSubjects,
  },
  Australia: {
    levels: ["Secondary School", "Senior Secondary", "Diploma / Technical", "Undergraduate", "Postgraduate", "Other"],
    streams: { "Secondary School": ["STEM", "Humanities", "Business", "Arts"], "Senior Secondary": ["ATAR pathway", "VET pathway", "General"], Undergraduate: ["Degree programme", "Exploring options"] },
    subjects: sharedSubjects,
  },
  India: {
    levels: ["Secondary (Class 9–10)", "Senior Secondary (Class 11–12)", "Diploma / Technical", "Undergraduate", "Postgraduate", "Other"],
    streams: { "Secondary (Class 9–10)": ["Science", "Commerce", "Humanities", "Skill subjects"], "Senior Secondary (Class 11–12)": ["Science", "Commerce", "Humanities", "Vocational"], Undergraduate: ["Major / Branch", "Exploring options"] },
    subjects: sharedSubjects,
  },
  Other: { levels: ["Secondary School", "Senior Secondary", "Diploma / Technical", "Technical / Vocational Certificate", "Undergraduate", "Postgraduate", "Other"], streams: {}, subjects: sharedSubjects },
};

export function educationOptionsFor(country) {
  return catalogs[country] || catalogs.Other;
}

export function studentStageFor(level = "") {
  const value = level.toLowerCase();

  if (/(matric|secondary|gcse|class 9|middle|high school)/.test(value) && !/(senior|sixth|a level)/.test(value)) {
    return "school";
  }
  if (/(intermediate|senior secondary|sixth form|a level|high school senior|class 11|class 12)/.test(value)) {
    return "senior_secondary";
  }
  if (/(diploma|dae|technical|vocational|vet|polytechnic|associate degree|short-cycle|post-secondary|college diploma)/.test(value)) {
    return "diploma";
  }
  if (/(bachelor|undergraduate)/.test(value)) return "undergraduate";
  if (/(master|graduate|postgraduate)/.test(value)) return "postgraduate";
  return "exploring";
}

const stageSubjects = {
  school: ["English", "Mathematics", "General Science", "Biology", "Chemistry", "Physics", "Computer Science", "Social Studies", "Arts & Design"],
  senior_secondary: ["English", "Mathematics", "Biology", "Chemistry", "Physics", "Computer Science", "Economics", "Business Studies", "Statistics", "Arts & Design"],
  diploma: ["Technical Drawing", "Applied Mathematics", "Applied Physics", "Computer Applications", "Workshop Practice", "Electrical Fundamentals", "Communication", "Project Work"],
  undergraduate: ["Programming", "Mathematics", "Research Methods", "Data Analysis", "Communication", "Project Management", "Design", "Finance & Economics"],
  postgraduate: ["Research Methods", "Advanced Data Analysis", "Specialisation Modules", "Academic Writing", "Leadership", "Project Management", "Professional Practice"],
  exploring: sharedSubjects,
};

export function subjectsFor(country, level, stream = "") {
  const stage = studentStageFor(level);
  const base = stageSubjects[stage] || sharedSubjects;
  const streamValue = stream.toLowerCase();

  if (country === "Pakistan" && stage === "school" && streamValue.includes("commerce")) {
    return ["English", "Mathematics", "Accounting", "Business Studies", "Economics", "Computer Science", "Arts & Design"];
  }
  if (country === "Pakistan" && stage === "school" && streamValue.includes("arts")) {
    return ["English", "Urdu", "Mathematics", "History", "Geography", "Civics", "Arts & Design"];
  }
  if (country === "Pakistan" && stage === "senior_secondary" && streamValue.includes("pre-medical")) {
    return ["English", "Biology", "Chemistry", "Physics", "Mathematics"];
  }
  if (country === "Pakistan" && stage === "senior_secondary" && (streamValue.includes("pre-engineering") || streamValue.includes("ics"))) {
    return ["English", "Mathematics", "Physics", "Computer Science", "Chemistry", "Statistics"];
  }
  return base;
}

export function assessmentFor(level) {
  const stage = studentStageFor(level);
  const assessments = {
    school: {
      title: "Explore your next school pathway",
      directionLabel: "Which area do you want to explore first?",
      directionOptions: ["Technology", "Health & Science", "Engineering", "Business", "Creative Arts", "Law", "Humanities & Social Impact"],
      contextLabel: "What decision do you need help with?",
      contextOptions: ["Choose my next stream", "Discover my strengths", "Build confidence in subjects"],
    },
    senior_secondary: {
      title: "Plan your degree pathway",
      directionLabel: "Which degree area interests you most?",
      directionOptions: ["Technology", "Health & Science", "Engineering", "Business", "Design & Media", "Law", "Architecture", "Social Sciences"],
      contextLabel: "What is your immediate goal?",
      contextOptions: ["Choose a degree", "Prepare for admission", "Build a portfolio"],
    },
    diploma: {
      title: "Turn technical training into a career pathway",
      directionLabel: "Which technical department are you preparing for?",
      directionOptions: ["Technology", "Engineering", "Architecture", "Health", "Business", "Design"],
      contextLabel: "What is your next goal?",
      contextOptions: ["Prepare for technical employment", "Build a practical portfolio", "Progress to a degree", "Prepare for industry certification"],
    },
    undergraduate: {
      title: "Shape your early career",
      directionLabel: "Which career field are you targeting?",
      directionOptions: ["Technology", "Data", "Engineering", "Business", "Design", "Education", "Health", "Law", "Architecture", "Media & Communication", "Social Sciences"],
      contextLabel: "What do you need next?",
      contextOptions: ["Choose a specialisation", "Prepare for internship", "Prepare for an entry-level role", "Build a portfolio"],
    },
    postgraduate: {
      title: "Define your specialist direction",
      directionLabel: "Which direction best describes your goal?",
      directionOptions: ["Research", "Advanced technical role", "Management & leadership", "Professional practice", "Teaching & academia"],
      contextLabel: "What do you need next?",
      contextOptions: ["Choose a specialisation", "Prepare for research", "Prepare for promotion", "Change career direction"],
    },
    exploring: {
      title: "Personalise your career direction",
      directionLabel: "Which field interests you most?",
      directionOptions: ["Technology", "Health & Science", "Engineering", "Business", "Design & Media", "Law", "Architecture", "Social Impact"],
      contextLabel: "What do you need help with?",
      contextOptions: ["Explore careers", "Identify strengths", "Plan next steps"],
    },
  };
  return assessments[stage];
}

const directionCatalog = {
  Technology: {
    interests: ["Software & apps", "Cybersecurity", "Data & AI", "Problem Solving", "Digital products", "Technology"],
    skills: ["Programming", "Web Development", "Database", "Python", "SQL", "Cybersecurity basics", "Problem Solving", "Communication"],
  },
  Data: {
    interests: ["Data & AI", "Mathematics", "Research", "Problem Solving", "Technology"],
    skills: ["Data Analysis", "Python", "SQL", "Statistics", "Excel", "Research", "Critical Thinking", "Communication"],
  },
  Engineering: {
    interests: ["How things work", "Mathematics", "Designing solutions", "Technology", "Problem Solving"],
    skills: ["Applied Mathematics", "Technical Drawing", "CAD / Design", "Project Management", "Problem Solving", "Safety awareness", "Communication"],
  },
  "Health & Science": {
    interests: ["Biology & health", "Helping People", "Research", "Science", "Problem Solving"],
    skills: ["Scientific research", "Data recording", "Communication", "Critical Thinking", "Ethics", "Teamwork", "Presentation"],
  },
  Health: {
    interests: ["Biology & health", "Helping People", "Research", "Science", "Problem Solving"],
    skills: ["Scientific research", "Data recording", "Communication", "Critical Thinking", "Ethics", "Teamwork", "Presentation"],
  },
  Business: {
    interests: ["Entrepreneurship", "Finance", "Management", "Marketing", "Communication"],
    skills: ["Excel", "Financial literacy", "Presentation", "Communication", "Leadership", "Project Management", "Problem Solving"],
  },
  "Creative Arts": {
    interests: ["Visual storytelling", "Creativity", "Design", "Media", "Communication"],
    skills: ["Design", "Creative tools", "Portfolio building", "Presentation", "Communication", "Creativity"],
  },
  "Design & Media": {
    interests: ["Visual storytelling", "Creativity", "Design", "Media", "Communication"],
    skills: ["Design", "Creative tools", "Portfolio building", "Presentation", "Communication", "Creativity"],
  },
  Design: {
    interests: ["Visual storytelling", "Creativity", "Design", "User experience", "Communication"],
    skills: ["Design", "Creative tools", "Portfolio building", "User research", "Presentation", "Communication"],
  },
  Law: {
    interests: ["Justice & policy", "Reading & writing", "Debate", "Research", "Helping People"],
    skills: ["Research", "Legal writing", "Critical Thinking", "Communication", "Presentation", "Ethics"],
  },
  Architecture: {
    interests: ["Built environment", "Design", "Mathematics", "Sustainability", "Creativity"],
    skills: ["Technical Drawing", "CAD / Design", "Design", "Project Management", "Presentation", "Problem Solving"],
  },
  "Media & Communication": {
    interests: ["Storytelling", "Media", "Communication", "Creativity", "Social impact"],
    skills: ["Writing", "Presentation", "Communication", "Content creation", "Research", "Creative tools"],
  },
  "Social Sciences": {
    interests: ["Helping People", "Society & culture", "Research", "Communication", "Social impact"],
    skills: ["Research", "Data Analysis", "Communication", "Critical Thinking", "Presentation", "Ethics"],
  },
  "Humanities & Social Impact": {
    interests: ["Helping People", "Society & culture", "Reading & writing", "Research", "Social impact"],
    skills: ["Research", "Writing", "Communication", "Critical Thinking", "Presentation", "Ethics"],
  },
  Education: {
    interests: ["Helping People", "Teaching", "Communication", "Creativity", "Social impact"],
    skills: ["Communication", "Presentation", "Lesson planning", "Research", "Leadership", "Creativity"],
  },
  Research: {
    interests: ["Research", "Data & AI", "Science", "Problem Solving", "Reading & writing"],
    skills: ["Research", "Data Analysis", "Academic writing", "Critical Thinking", "Presentation", "Project Management"],
  },
};

const transferableInterests = ["Problem Solving", "Communication", "Creativity", "Helping People", "Research"];
const transferableSkills = ["Communication", "Problem Solving", "Critical Thinking", "Presentation", "Teamwork"];

const directionAliases = {
  "Advanced technical role": "Technology",
  "Management & leadership": "Business",
  "Professional practice": "Social Sciences",
  "Teaching & academia": "Education",
  "Social Impact": "Social Sciences",
};

export function interestsFor(direction = "") {
  const matches = directionCatalog[directionAliases[direction] || direction]?.interests || [];
  return [...new Set([...matches, ...transferableInterests])];
}

export function skillsFor(direction = "") {
  const matches = directionCatalog[directionAliases[direction] || direction]?.skills || [];
  return [...new Set([...matches, ...transferableSkills])];
}
