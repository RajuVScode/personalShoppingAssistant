import { Twitter, Linkedin } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full bg-gray-100 py-4 px-6 border-t" data-testid="footer">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="bg-[#1565C0] text-white font-bold px-2 py-1 rounded text-sm">
            PSA
          </div>
          <span className="text-xs text-gray-600" style={{ fontFamily: 'Calibri, sans-serif' }}>AI Shopping Assistant</span>
        </div>
        
        <nav className="flex items-center gap-4 text-sm text-gray-600" style={{ fontFamily: 'Calibri, sans-serif' }}>
          <a href="#" className="hover:text-[#1565C0] transition-colors" data-testid="link-about">About</a>
          <a href="#" className="hover:text-[#1565C0] transition-colors" data-testid="link-pricing">Pricing</a>
          <a href="#" className="hover:text-[#1565C0] transition-colors" data-testid="link-blog">Blog</a>
          <a href="#" className="hover:text-[#1565C0] transition-colors" data-testid="link-help">Help Center</a>
          <a href="#" className="hover:text-[#1565C0] transition-colors" data-testid="link-contact">Contact</a>
        </nav>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <a href="#" className="hover:text-[#1565C0] transition-colors flex items-center gap-1" data-testid="link-twitter">
              <Twitter className="w-4 h-4" />
              Twitter
            </a>
            <span className="text-gray-400">•</span>
            <a href="#" className="hover:text-[#1565C0] transition-colors flex items-center gap-1" data-testid="link-linkedin">
              <Linkedin className="w-4 h-4" />
              LinkedIn
            </a>
          </div>
        </div>
      </div>
      <div className="text-center text-xs text-gray-500 mt-3" style={{ fontFamily: 'Calibri, sans-serif' }}>
        © 2025 PSA. All rights reserved.
      </div>
    </footer>
  );
}
