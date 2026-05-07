def normalize_list(items):
    if not items:
        return set()

    return set(
        str(item).strip().lower()
        for item in items
        if str(item).strip()
    )


def normalize_text(value):
    return str(value or "").strip().lower()


def find_missing_skills(student_skills, required_skills):
    student_skill_set = normalize_list(student_skills)
    required_skill_set = normalize_list(required_skills)

    missing_skills = required_skill_set.difference(student_skill_set)

    return sorted(list(missing_skills))


def is_resource_relevant(resource, missing_skills, career_field=None):
    resource_skill = normalize_text(resource.skill)
    resource_field = normalize_text(resource.career_field)
    target_field = normalize_text(career_field)

    missing_skill_set = set(
        normalize_text(skill)
        for skill in missing_skills
    )

    skill_match = resource_skill in missing_skill_set
    field_match = bool(target_field and resource_field == target_field)

    return skill_match or field_match