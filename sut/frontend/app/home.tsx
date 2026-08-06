import React from 'react';
import { useHome } from '@/src/controllers/useHome';
import { HomeView } from '@/src/views/HomeView';

export default function HomeScreen() {
  const homeController = useHome();
  return <HomeView controller={homeController} />;
}
