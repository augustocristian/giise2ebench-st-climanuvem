import React from 'react';
import { useProfile } from '@/src/controllers/useProfile';
import { ProfileView } from '@/src/views/ProfileView';

export default function ProfileScreen() {
  const profileController = useProfile();
  return <ProfileView controller={profileController} />;
}
