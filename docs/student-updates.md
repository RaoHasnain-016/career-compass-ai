# Student notifications and study options

The student menu links to Notifications and Study Options. The dashboard and recommendation bells show recent notifications and unread counts. The inbox checks for updates every five minutes while visible and immediately after an in-app profile or active-career change. Opening a bell refreshes a list last checked more than 30 seconds ago. Read status follows the signed-in student across devices.

Profile creation, changed profile details, active-career changes and recommendation generation create personal inbox events. To publish an app release note, add an entry with a unique, permanent ID to `PLATFORM_NOTICES` in `backend/app/services/student_updates_service.py` and include it in the release.

Career updates come from the listed official providers in `backend/app/services/career_news_service.py`. The backend checks public feeds on demand with a shared five-minute cache and matches items to profiles afterwards. It never sends student records to the sources. Date, country, field and education-stage filters determine relevance. Selecting an active career narrows field news to that career's field and filters articles that name another supported occupation. Without an active career, the inbox uses the student's profile, saved careers and recommendations. Feed coverage can produce an empty result for a valid profile when publishers have no matching items.

Study Options uses the active career first, followed by the profile direction, academic stream, saved careers and sufficiently strong recommendations. The shortlist covers Pakistan, the United Kingdom, the United States, Canada, Australia and India. Link checks indicate reachability and show the check date. Confirm admission status, qualification equivalence, subject prerequisites, deadlines, fees and accreditation with the institution or regulator.

Fresh local setups include the two notification tables. The existing EC2 app startup creates the tables during its schema patch step. For environments that manage schema changes separately, apply `database/migrations/20261126_student_updates.sql` before starting the updated backend.
