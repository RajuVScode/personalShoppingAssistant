import logoImage from '@assets/image_1768456487731.png';

export default function Logo({ className = "h-12" }: { className?: string }) {
  return (
    <img 
      src={logoImage}
      alt="tensai AgentVerse for Retail"
      className={className}
    />
  );
}
