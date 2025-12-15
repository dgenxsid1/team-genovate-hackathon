
import React, { useState, useEffect } from 'react';

const loadingMessages = [
  "Parsing input data...",
  "Initializing Python analysis environment...",
  "Extracting location to query databases...",
  "Querying BigQuery for market & risk data...",
  "Engaging Gemini predictive model...",
  "Synthesizing data points and checking for discrepancies...",
  "Generating final memo...",
  "Almost there..."
];

export const LoadingIndicator: React.FC = () => {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prevIndex) => (prevIndex + 1) % loadingMessages.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-gray-800/50 border border-gray-700 rounded-xl text-center">
      <div className="w-12 h-12 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4"></div>
      <p className="text-lg font-semibold text-gray-200">Generating Analysis</p>
      <p className="text-gray-400 mt-2 transition-opacity duration-500">
        {loadingMessages[messageIndex]}
      </p>
    </div>
  );
};
