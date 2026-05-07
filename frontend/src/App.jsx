import { BrowserRouter, Routes, Route } from "react-router-dom";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import EmailVerification from "./pages/EmailVerification";
import WelcomeOnboarding from "./pages/WelcomeOnboarding";
import Dashboard from "./pages/Dashboard";
import ProfileSetup from "./pages/ProfileSetup";
import InterestSelection from "./pages/InterestSelection";
import SkillsSelection from "./pages/SkillsSelection";
import AssessmentSummary from "./pages/AssessmentSummary";
import RecommendationLoading from "./pages/RecommendationLoading";
import Recommendations from "./pages/Recommendations";
import CareerDetail from "./pages/CareerDetail";
import Roadmap from "./pages/Roadmap";
import RoadmapStageDetail from "./pages/RoadmapStageDetail";
import SkillGap from "./pages/SkillGap";
import LearningResources from "./pages/LearningResources";
import ResourceDetail from "./pages/ResourceDetail";
import Chatbot from "./pages/Chatbot";
import ChatHistory from "./pages/ChatHistory";
import SavedCareers from "./pages/SavedCareers";
import CompareCareers from "./pages/CompareCareers";
import StudentProfile from "./pages/StudentProfile";
import Settings from "./pages/Settings";
import HelpFAQ from "./pages/HelpFAQ";
import ContactUs from "./pages/ContactUs";
import AboutProject from "./pages/AboutProject";
import NoRecommendationFound from "./pages/NoRecommendationFound";
import SplashLoading from "./pages/SplashLoading";
import TermsPrivacy from "./pages/TermsPrivacy";
import NotFound from "./pages/NotFound";

import AdminDashboard from "./pages/admin/AdminDashboard";
import ManageUsers from "./pages/admin/ManageUsers";
import ManageCareers from "./pages/admin/ManageCareers";
import ManageResources from "./pages/admin/ManageResources";
import ManageRoadmaps from "./pages/admin/ManageRoadmaps";
import AdminReports from "./pages/admin/AdminReports";

import ProtectedRoute from "./components/ProtectedRoute";
import FloatingChatbotButton from "./components/FloatingChatbotButton";

function protectedPage(page) {
  return <ProtectedRoute>{page}</ProtectedRoute>;
}

function App() {
  return (
    <BrowserRouter>
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

        <Route path="/admin" element={protectedPage(<AdminDashboard />)} />
        <Route path="/admin/users" element={protectedPage(<ManageUsers />)} />
        <Route path="/admin/careers" element={protectedPage(<ManageCareers />)} />
        <Route path="/admin/roadmaps" element={protectedPage(<ManageRoadmaps />)} />
        <Route path="/admin/resources" element={protectedPage(<ManageResources />)} />
        <Route path="/admin/reports" element={protectedPage(<AdminReports />)} />

        <Route path="*" element={<NotFound />} />
      </Routes>

      <FloatingChatbotButton />
    </BrowserRouter>
  );
}

export default App;