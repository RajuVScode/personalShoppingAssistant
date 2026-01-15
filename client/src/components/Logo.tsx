export default function Logo({ className = "h-12" }: { className?: string }) {
  return (
    <img 
      src="/agentverse-logo.png"
      alt="tensai AgentVerse for Retail"
      className={className}
    />
  );
}
