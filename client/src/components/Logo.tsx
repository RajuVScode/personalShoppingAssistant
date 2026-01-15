import logoImage from '@assets/agentverse-logo-CXLdSwax_1768456021802.png';

export default function Logo({ className = "h-12" }: { className?: string }) {
  return (
    <img 
      src={logoImage}
      alt="tensai AgentVerse for Retail"
      className={className}
      style={{ backgroundColor: 'white', padding: '4px', borderRadius: '4px' }}
    />
  );
}
