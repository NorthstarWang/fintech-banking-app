import React from 'react';

export const BackgroundEffects: React.FC = () => {
  return (
    <>
      {/* Background overlay for better content readability */}
      <div className="bg-overlay" />
      
      {/* Additional floating gradient bubbles for finance theme */}
      <div
        className="fixed w-[30vw] h-[30vw] max-w-[400px] max-h-[400px] 
                   top-[20%] left-[10%] rounded-full z-[-1] 
                   animate-float opacity-30"
        style={{
          background: `radial-gradient(circle at 40% 40%, 
            var(--vibrant-indigo) 0%, 
            var(--vibrant-blue) 45%, 
            transparent 70%)`,
          filter: 'blur(80px)',
          animationDelay: '-5s',
        }}
      />
      
      <div
        className="fixed w-[25vw] h-[25vw] max-w-[350px] max-h-[350px] 
                   bottom-[15%] right-[20%] rounded-full z-[-1] 
                   animate-float-alt opacity-25"
        style={{
          background: `radial-gradient(circle at 60% 60%, 
            var(--vibrant-emerald) 0%, 
            var(--vibrant-teal) 45%, 
            transparent 70%)`,
          filter: 'blur(90px)',
          animationDelay: '-15s',
        }}
      />
      
      {/* Subtle grid pattern overlay for professional look */}
      <div
        className="fixed inset-0 z-[-1] opacity-[0.015]"
        style={{
          backgroundImage: `
            linear-gradient(var(--text-2) 1px, transparent 1px),
            linear-gradient(90deg, var(--text-2) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
        }}
      />
    </>
  );
};

export default BackgroundEffects;