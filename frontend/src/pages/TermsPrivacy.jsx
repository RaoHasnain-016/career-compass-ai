import Navbar from "../components/Navbar";
import "../styles/static-page.css";

export default function TermsPrivacy() {
  return (
    <>
      <Navbar />
      <main className="public-static-page">
        <section className="public-static-hero">
          <span>Terms & Privacy</span>
          <h1>Responsible AI Guidance</h1>
          <p>
            Career Compass AI uses student profile data to provide advisory recommendations,
            not guaranteed academic, employment, or admission outcomes.
          </p>
        </section>

        <section className="public-static-card terms-card">
          <h2>Data Collection</h2>
          <p>
            Student profile fields, recommendations, saved careers, and chat history are used
            only to personalize the logged-in student experience.
          </p>

          <h2>Authentication</h2>
          <p>
            Protected requests are tied to the current Firebase account and require a valid
            Firebase ID token.
          </p>

          <h2>AI Disclaimer</h2>
          <p>
            Recommendations are educational guidance. Students should review options with
            mentors, counselors, and official academic sources before making final decisions.
          </p>
        </section>
      </main>
    </>
  );
}
