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
    levels: ["Matric", "Intermediate", "Bachelor", "Master", "Other"],
    streams: {
      Matric: ["Science", "Computer Science", "Arts & Humanities", "Commerce"],
      Intermediate: ["Pre-Medical", "Pre-Engineering", "ICS", "ICom", "FA / Humanities"],
      Bachelor: ["Computing & Technology", "Health Sciences", "Engineering", "Business & Management", "Social Sciences", "Arts & Design"],
    },
    subjects: sharedSubjects,
  },
  "United States": {
    levels: ["Middle / High School", "High School Senior", "Undergraduate", "Graduate", "Other"],
    streams: { "Middle / High School": ["STEM", "Humanities", "Business", "Arts"], "High School Senior": ["AP / Honors STEM", "AP / Honors Humanities", "Career & Technical Education", "General"], Undergraduate: ["Major / Concentration", "Undeclared / Exploring"] },
    subjects: sharedSubjects,
  },
  "United Kingdom": {
    levels: ["Secondary / GCSE", "Sixth Form / A Level", "Undergraduate", "Postgraduate", "Other"],
    streams: { "Secondary / GCSE": ["STEM", "Humanities", "Arts", "Business"], "Sixth Form / A Level": ["Science", "Mathematics & Computing", "Humanities", "Business & Economics", "Creative Arts"], Undergraduate: ["Degree programme", "Exploring options"] },
    subjects: sharedSubjects,
  },
  Canada: {
    levels: ["Secondary School", "Senior Secondary", "Undergraduate", "Graduate", "Other"],
    streams: { "Secondary School": ["STEM", "Humanities", "Business", "Arts"], "Senior Secondary": ["University preparation", "College preparation", "Skilled trades", "General"], Undergraduate: ["Major / Concentration", "Exploring options"] },
    subjects: sharedSubjects,
  },
  Australia: {
    levels: ["Secondary School", "Senior Secondary", "Undergraduate", "Postgraduate", "Other"],
    streams: { "Secondary School": ["STEM", "Humanities", "Business", "Arts"], "Senior Secondary": ["ATAR pathway", "VET pathway", "General"], Undergraduate: ["Degree programme", "Exploring options"] },
    subjects: sharedSubjects,
  },
  India: {
    levels: ["Secondary (Class 9–10)", "Senior Secondary (Class 11–12)", "Undergraduate", "Postgraduate", "Other"],
    streams: { "Secondary (Class 9–10)": ["Science", "Commerce", "Humanities", "Skill subjects"], "Senior Secondary (Class 11–12)": ["Science", "Commerce", "Humanities", "Vocational"], Undergraduate: ["Major / Branch", "Exploring options"] },
    subjects: sharedSubjects,
  },
  Other: { levels: ["Secondary School", "Senior Secondary", "Undergraduate", "Postgraduate", "Other"], streams: {}, subjects: sharedSubjects },
};

export function educationOptionsFor(country) {
  return catalogs[country] || catalogs.Other;
}
