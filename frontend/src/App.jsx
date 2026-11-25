import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

const Landing = lazy(() => import("./pages/Landing"));
const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const EmailVerification = lazy(() => import("./pages/EmailVerification"));
const WelcomeOnboarding = lazy(() => import("./pages/WelcomeOnboarding"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const ProfileSetup = lazy(() => import("./pages/ProfileSetup"));
const InterestSelection = lazy(() => import("./pages/InterestSelection"));
const SkillsSelection = lazy(() => import("./pages/SkillsSelection"));
const AssessmentSummary = lazy(() => import("./pages/AssessmentSummary"));
const RecommendationLoading = lazy(() => import("./pages/RecommendationLoading"));
const Recommendations = lazy(() => import("./pages/Recommendations"));
const CareerDetail = lazy(() => import("./pages/CareerDetail"));
const Roadmap = lazy(() => import("./pages/Roadmap"));
const RoadmapStageDetail = lazy(() => import("./pages/RoadmapStageDetail"));
const SkillGap = lazy(() => import("./pages/SkillGap"));
const LearningResources = lazy(() => import("./pages/LearningResources"));
const ResourceDetail = lazy(() => import("./pages/ResourceDetail"));
const Chatbot = lazy(() => import("./pages/Chatbot"));
const ChatHistory = lazy(() => import("./pages/ChatHistory"));
const SavedCareers = lazy(() => import("./pages/SavedCareers"));
const CompareCareers = lazy(() => import("./pages/CompareCareers"));
const StudentProfile = lazy(() => import("./pages/StudentProfile"));
const Settings = lazy(() => import("./pages/Settings"));
const HelpFAQ = lazy(() => import("./pages/HelpFAQ"));
const ContactUs = lazy(() => import("./pages/ContactUs"));
const AboutProject = lazy(() => import("./pages/AboutProject"));
const NoRecommendationFound = lazy(() => import("./pages/NoRecommendationFound"));
const SplashLoading = lazy(() => import("./pages/SplashLoading"));
const TermsPrivacy = lazy(() => import("./pages/TermsPrivacy"));
const NotFound = lazy(() => import("./pages/NotFound"));

const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const ManageUsers = lazy(() => import("./pages/admin/ManageUsers"));
const ManageCareers = lazy(() => import("./pages/admin/ManageCareers"));
const ManageResources = lazy(() => import("./pages/admin/ManageResources"));
const ManageRoadmaps = lazy(() => import("./pages/admin/ManageRoadmaps"));
const AdminReports = lazy(() => import("./pages/admin/AdminReports"));

// These modules import Firebase and icon code. Loading them only when the
// visitor opens a protected route keeps the public landing page lightweight.
const ProtectedRoute = lazy(() => import("./components/ProtectedRoute"));
const AdminRoute = lazy(() => import("./components/AdminRoute"));
const FloatingChatbotButton = lazy(() => import("./components/FloatingChatbotButton"));

function protectedPage(page) {
  return <ProtectedRoute>{page}</ProtectedRoute>;
}

function adminPage(page) {
  return <ProtectedRoute><AdminRoute>{page}</AdminRoute></ProtectedRoute>;
}

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div className="app-route-loader">Loading...</div>}>
        <Routes>
        <Route path="/" element={<Landing />} />

        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/verify-email" element={<EmailVerification />} />

        <Route path="/welcome" element={protectedPage(<WelcomeOnboarding />)} />
        <Route path="/dashboard" element={protectedPage(<Dashboard />)} />
        <Route path="/profile-setup" element={protectedPage(<ProfileSetup />)} />
        <Route path="/interests" element={protectedPage(<InterestSelection />)} />
        <Route path="/skills" element={protectedPage(<SkillsSelection />)} />
        <Route path="/assessment-summary" element={protectedPage(<AssessmentSummary />)} />
        <Route path="/recommendation-loading" element={protectedPage(<RecommendationLoading />)} />
        <Route path="/recommendations" element={protectedPage(<Recommendations />)} />
        <Route path="/career/:id" element={protectedPage(<CareerDetail />)} />
        <Route path="/roadmap" element={protectedPage(<Roadmap />)} />
        <Route path="/roadmap-stage" element={protectedPage(<RoadmapStageDetail />)} />
        <Route path="/skill-gap" element={protectedPage(<SkillGap />)} />
        <Route path="/resources" element={protectedPage(<LearningResources />)} />
        <Route path="/resource/:id" element={protectedPage(<ResourceDetail />)} />
        <Route path="/chatbot" element={protectedPage(<Chatbot />)} />
        <Route path="/chat-history" element={protectedPage(<ChatHistory />)} />
        <Route path="/saved-careers" element={protectedPage(<SavedCareers />)} />
        <Route path="/compare-careers" element={protectedPage(<CompareCareers />)} />
        <Route path="/profile" element={protectedPage(<StudentProfile />)} />
        <Route path="/settings" element={protectedPage(<Settings />)} />
        <Route path="/help" element={protectedPage(<HelpFAQ />)} />
        <Route path="/no-recommendation" element={protectedPage(<NoRecommendationFound />)} />

        <Route path="/contact" element={<ContactUs />} />
        <Route path="/about" element={<AboutProject />} />
        <Route path="/loading" element={<SplashLoading />} />
        <Route path="/terms" element={<TermsPrivacy />} />

        <Route path="/admin" element={adminPage(<AdminDashboard />)} />
        <Route path="/admin/users" element={adminPage(<ManageUsers />)} />
        <Route path="/admin/careers" element={adminPage(<ManageCareers />)} />
        <Route path="/admin/roadmaps" element={adminPage(<ManageRoadmaps />)} />
        <Route path="/admin/resources" element={adminPage(<ManageResources />)} />
        <Route path="/admin/reports" element={adminPage(<AdminReports />)} />

        <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>

      <Suspense fallback={null}>
        <FloatingChatbotButton />
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
