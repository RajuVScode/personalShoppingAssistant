export default function Logo({ className = "h-12" }: { className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 460 110" 
      role="img" 
      aria-label="PSA logo"
      className={className}
    >
      <defs>
        <filter id="ds" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="1" stdDeviation="2" floodColor="#000" floodOpacity="0.35" />
        </filter>
      </defs>

      <g filter="url(#ds)">
        <rect x="10" y="30" width="80" height="70" rx="12" fill="#fff" stroke="#fff" strokeWidth="3"/>
        <path d="M35,30 V20 A20,20 0 0 1 65,20 V30" fill="none" stroke="#fff" strokeWidth="4" strokeLinecap="round"/>
        <circle cx="35" cy="55" r="5" fill="#1a65b3"/>
        <circle cx="65" cy="55" r="5" fill="#1a65b3"/>
        <path d="M35,75 Q50,88 65,75" stroke="#1a65b3" strokeWidth="3" strokeLinecap="round" fill="none"/>
      </g>

      <text x="110" y="65" fontFamily="Calibri, Segoe UI, Arial, sans-serif" fontSize="56" fontWeight="700" fill="#fff">PSA</text>
      <text x="110" y="90" fontFamily="Calibri, Segoe UI, Arial, sans-serif" fontSize="18" fontWeight="400" fill="#fff" opacity="0.9">AI Shopping Assistant</text>
    </svg>
  );
}
