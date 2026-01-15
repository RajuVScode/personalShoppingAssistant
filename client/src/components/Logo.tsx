export default function Logo({ className = "h-12" }: { className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 380 60" 
      role="img" 
      aria-label="tensai logo"
      className={className}
    >
      <circle cx="28" cy="30" r="24" fill="#C9A961"/>
      <circle cx="28" cy="22" r="8" fill="#fff"/>
      <ellipse cx="28" cy="42" rx="14" ry="10" fill="#fff"/>
      
      <text x="62" y="32" fontFamily="Arial, sans-serif" fontSize="28" fontWeight="400" fill="#fff" letterSpacing="-0.5">
        tensai
      </text>
      <text x="156" y="22" fontFamily="Arial, sans-serif" fontSize="10" fill="#fff">®</text>
      
      <text x="62" y="48" fontFamily="Arial, sans-serif" fontSize="12" fill="#fff" opacity="0.85">
        AgentVerse for Retail
      </text>
      
      <rect x="200" y="12" width="100" height="36" rx="6" fill="#fff"/>
      <text x="250" y="26" fontFamily="Arial, sans-serif" fontSize="10" fontWeight="600" fill="#1565C0" textAnchor="middle">
        Personal
      </text>
      <text x="250" y="40" fontFamily="Arial, sans-serif" fontSize="10" fontWeight="600" fill="#1565C0" textAnchor="middle">
        Shopping
      </text>
    </svg>
  );
}
