import React from 'react';
import { useWelcome } from '@/src/controllers/useWelcome';
import { WelcomeView } from '@/src/views/WelcomeView';

export default function WelcomeScreen() {
  const welcomeController = useWelcome();
  
  return <WelcomeView controller={welcomeController} />;
}
