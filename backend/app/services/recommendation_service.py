def safe_list(value):
    if not value:
        return []
    return value


def normalize_list(items):
    return set(
        str(item).strip().lower()
        for item in safe_list(items)
        if str(item).strip()
    )


def calculate_percentage_match(student_items, career_items):
    student_set = normalize_list(student_items)
    career_set = normalize_list(career_items)

    if not career_set:
        return 0, [], []

    matched = student_set.intersection(career_set)
    missing = career_set.difference(student_set)

    percentage = len(matched) / len(career_set)

    return percentage, sorted(list(matched)), sorted(list(missing))


def calculate_academic_score(profile, career):
    marks = float(profile.marks_cgpa) if profile.marks_cgpa is not None else 0
    minimum_marks = float(career.minimum_marks) if career.minimum_marks is not None else 0

    if minimum_marks <= 0:
        return 20, "eligible"

    if marks >= minimum_marks:
        return 20, "eligible"

    # Partial score if student is close to required marks
    academic_score = max((marks / minimum_marks) * 20, 0)

    if academic_score >= 15:
        status = "near_eligible"
    else:
        status = "below_requirement"

    return round(academic_score, 2), status


def calculate_preference_score(profile, career):
    study_preference = str(profile.study_preference or "").lower()
    career_field = str(career.field or "").lower()
    difficulty = str(career.difficulty_level or "").lower()

    score = 0

    # Simple practical preference matching
    if "online" in study_preference:
        if career_field in ["technology", "business", "design", "data"]:
            score += 5

    if "practical" in study_preference or "project" in study_preference:
        if career_field in ["technology", "engineering", "design"]:
            score += 5

    if "research" in study_preference:
        if career_field in ["medical", "science", "data"]:
            score += 5

    if "easy" in study_preference and difficulty == "easy":
        score += 5
    elif "moderate" in study_preference and difficulty == "moderate":
        score += 5
    elif "challenging" in study_preference and difficulty in ["difficult", "hard"]:
        score += 5

    return min(score, 10)


def get_confidence_level(score):
    if score >= 80:
        return "Very Strong Match"
    if score >= 65:
        return "Strong Match"
    if score >= 50:
        return "Moderate Match"
    if score >= 35:
        return "Weak Match"
    return "Very Weak Match"


def generate_recommendation_analysis(profile, career):
    academic_score, eligibility_status = calculate_academic_score(profile, career)

    interest_ratio, matched_interests, missing_interests = calculate_percentage_match(
        profile.interests,
        career.related_interests
    )

    skill_ratio, matched_skills, missing_skills = calculate_percentage_match(
        profile.skills,
        career.required_skills
    )

    subject_ratio, matched_subjects, missing_subjects = calculate_percentage_match(
        profile.favorite_subjects,
        career.required_subjects
    )

    preference_score = calculate_preference_score(profile, career)

    interest_score = interest_ratio * 25
    skill_score = skill_ratio * 25
    subject_score = subject_ratio * 20

    total_score = (
        academic_score
        + interest_score
        + skill_score
        + subject_score
        + preference_score
    )

    total_score = round(min(total_score, 100), 2)

    confidence_level = get_confidence_level(total_score)

    explanation = generate_human_explanation(
        career=career,
        score=total_score,
        confidence_level=confidence_level,
        eligibility_status=eligibility_status,
        matched_interests=matched_interests,
        matched_skills=matched_skills,
        matched_subjects=matched_subjects,
        missing_skills=missing_skills,
        missing_subjects=missing_subjects,
    )

    improvement_advice = generate_improvement_advice(
        career=career,
        missing_skills=missing_skills,
        missing_subjects=missing_subjects,
        eligibility_status=eligibility_status,
    )

    return {
        "score": total_score,
        "confidence_level": confidence_level,
        "eligibility_status": eligibility_status,
        "matched_interests": matched_interests,
        "matched_skills": matched_skills,
        "matched_subjects": matched_subjects,
        "missing_interests": missing_interests,
        "missing_skills": missing_skills,
        "missing_subjects": missing_subjects,
        "improvement_advice": improvement_advice,
        "explanation": explanation,
    }


def generate_human_explanation(
    career,
    score,
    confidence_level,
    eligibility_status,
    matched_interests,
    matched_skills,
    matched_subjects,
    missing_skills,
    missing_subjects,
):
    parts = []

    parts.append(
        f"{career.title} is a {confidence_level.lower()} for you with a {score}% match score."
    )

    if eligibility_status == "eligible":
        parts.append(
            "Your academic performance meets the basic requirement for this career."
        )
    elif eligibility_status == "near_eligible":
        parts.append(
            "Your academic performance is close to the required level, so this career is still possible with improvement."
        )
    else:
        parts.append(
            "Your academic score is currently below the recommended requirement for this career."
        )

    if matched_interests:
        parts.append(
            f"It matches your interests in {', '.join(matched_interests)}."
        )

    if matched_skills:
        parts.append(
            f"Your existing skills such as {', '.join(matched_skills)} support this career path."
        )

    if matched_subjects:
        parts.append(
            f"Your favorite subjects like {', '.join(matched_subjects)} are relevant to this field."
        )

    if missing_skills:
        parts.append(
            f"To improve your match, you should work on {', '.join(missing_skills)}."
        )

    if missing_subjects:
        parts.append(
            f"You may also need stronger understanding of {', '.join(missing_subjects)}."
        )

    return " ".join(parts)


def generate_improvement_advice(
    career,
    missing_skills,
    missing_subjects,
    eligibility_status,
):
    advice = []

    if eligibility_status == "below_requirement":
        advice.append(
            "Improve your academic performance before choosing this path as a primary option."
        )
    elif eligibility_status == "near_eligible":
        advice.append(
            "You are close to the academic requirement, so improving marks/CGPA can make this career more suitable."
        )

    if missing_skills:
        top_skills = missing_skills[:3]
        advice.append(
            f"Start learning these important skills first: {', '.join(top_skills)}."
        )

    if missing_subjects:
        top_subjects = missing_subjects[:2]
        advice.append(
            f"Focus more on these subjects: {', '.join(top_subjects)}."
        )

    if not advice:
        advice.append(
            f"You already have a good foundation for {career.title}. Continue building projects, practical experience, and career-specific knowledge."
        )

    return " ".join(advice)