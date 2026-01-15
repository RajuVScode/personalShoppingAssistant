export default function Logo({ className = "h-12" }: { className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 380 60" 
      role="img" 
      aria-label="tensai logo"
      className={className}
    >
      <circle cx="30" cy="30" r="24" fill="#C9A961"/>
      <circle cx="30" cy="22" r="7" fill="none" stroke="#fff" strokeWidth="2"/>
      <path d="M18 42 Q30 32 42 42" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round"/>
      
      <text x="64" y="35" fontFamily="Arial, sans-serif" fontSize="28" fontWeight="300" fill="#fff" letterSpacing="1">
        tensai
      </text>
      <text x="156" y="22" fontFamily="Arial, sans-serif" fontSize="10" fill="#fff">®</text>
      
      <text x="64" y="50" fontFamily="Arial, sans-serif" fontSize="12" fill="#fff" opacity="0.85">
        AgentVerse for Retail
      </text>
      
      <rect x="210" y="12" width="95" height="36" rx="4" fill="#3949AB"/>
      <text x="257" y="27" fontFamily="Arial, sans-serif" fontSize="10" fontWeight="600" fill="#fff" textAnchor="middle">Personal</text>
      <text x="257" y="40" fontFamily="Arial, sans-serif" fontSize="10" fontWeight="600" fill="#fff" textAnchor="middle">Shopping</text>
    </svg>
  );
}
