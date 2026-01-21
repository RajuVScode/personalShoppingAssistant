import { Twitter, Linkedin } from "lucide-react";
import "../styles/footer.css";

export default function Footer() {
  return (
    <footer className="footer" id="footer" data-testid="footer">
      <div className="footer-inner" id="footer-inner">
        <div className="footer-brand" id="footer-brand">
          <div className="footer-brand-logo">
            PSA
          </div>
          <span className="footer-brand-text">AI Shopping Assistant</span>
        </div>
        
        <nav className="footer-nav" id="footer-nav">
          <a href="#" className="footer-nav-link" id="footer-link-about" data-testid="link-about">About</a>
          <a href="#" className="footer-nav-link" id="footer-link-pricing" data-testid="link-pricing">Pricing</a>
          <a href="#" className="footer-nav-link" id="footer-link-blog" data-testid="link-blog">Blog</a>
          <a href="#" className="footer-nav-link" id="footer-link-help" data-testid="link-help">Help Center</a>
          <a href="#" className="footer-nav-link" id="footer-link-contact" data-testid="link-contact">Contact</a>
        </nav>
        
        <div className="footer-social" id="footer-social">
          <div className="footer-social-links">
            <a href="#" className="footer-social-link" id="footer-link-twitter" data-testid="link-twitter">
              <Twitter className="footer-social-icon" />
              Twitter
            </a>
            <span className="footer-social-divider">•</span>
            <a href="#" className="footer-social-link" id="footer-link-linkedin" data-testid="link-linkedin">
              <Linkedin className="footer-social-icon" />
              LinkedIn
            </a>
          </div>
        </div>
      </div>
      <div className="footer-copyright" id="footer-copyright">
        © 2025 PSA. All rights reserved.
      </div>
    </footer>
  );
}
