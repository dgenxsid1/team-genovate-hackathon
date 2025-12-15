
import React from 'react';
import { ChartBarIcon } from './icons/ChartBarIcon';
import { DocumentTextIcon } from './icons/DocumentTextIcon';
import { ScaleIcon } from './icons/ScaleIcon';

const FeatureCard: React.FC<{ icon: React.ReactNode; title: string; description: string }> = ({ icon, title, description }) => (
  <div className="flex items-start gap-4">
    <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center bg-gray-700 rounded-lg text-cyan-400">
      {icon}
    </div>
    <div>
      <h4 className="font-semibold text-gray-200">{title}</h4>
      <p className="text-gray-400 text-sm">{description}</p>
    </div>
  </div>
);

export const WelcomeScreen: React.FC = () => {
  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-8 space-y-6">
      <h3 className="text-xl font-bold text-center text-gray-200">Welcome to the Future of Real Estate Analysis</h3>
      <p className="text-center text-gray-400">
        Leverage AI to transform hours of research into minutes of insight. Get started by uploading your property data file above.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
        <FeatureCard 
          icon={<DocumentTextIcon className="h-6 w-6" />}
          title="Comprehensive Memos"
          description="Generate full deal memos including executive summaries, property details, and risk assessments from your data."
        />
        <FeatureCard 
          icon={<ChartBarIcon className="h-6 w-6" />}
          title="Data-Driven Predictions"
          description="Analyze market trends and financial scenarios using only the data you provide."
        />
        <FeatureCard 
          icon={<ScaleIcon className="h-6 w-6" />}
          title="Rapid Valuations"
          description="Receive preliminary collateral valuations based on sales comps and income approaches found in your data."
        />
      </div>
    </div>
  );
};
