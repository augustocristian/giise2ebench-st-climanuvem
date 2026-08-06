import React from 'react';
import { useRegister } from '@/src/controllers/useRegister';
import { RegisterView } from '@/src/views/RegisterView';

export default function RegisterScreen() {
  const registerController = useRegister();
  
  return <RegisterView controller={registerController} />;
}
