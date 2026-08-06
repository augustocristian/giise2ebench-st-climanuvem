import React from 'react';
import { useAuth } from '@/src/controllers/useAuth';
import { AuthView } from '@/src/views/AuthView';

export default function LoginScreen() {
  const authController = useAuth();
  return <AuthView controller={authController} />;
}
