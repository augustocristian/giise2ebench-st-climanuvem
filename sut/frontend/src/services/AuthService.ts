import { auth } from '@/src/config/firebaseConfig';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendEmailVerification,
  sendPasswordResetEmail,
  signOut,
  onAuthStateChanged,
  updateProfile,
  deleteUser,
  GoogleAuthProvider,
  signInWithCredential,
  signInAnonymously,
  type User as FirebaseUser,
  type Unsubscribe,
} from 'firebase/auth';
import type { User, AuthResponse } from '@/src/models/User';

const mapFirebaseUser = (fbUser: Pick<FirebaseUser, 'uid' | 'displayName' | 'email' | 'isAnonymous'>, displayNameOverride?: string): User => ({
  uid: fbUser.uid,
  displayName: displayNameOverride ?? fbUser.displayName ?? undefined,
  email: fbUser.email ?? '',
  isAnonymous: fbUser.isAnonymous,
});

const authError = (error: any): AuthResponse => ({
  success: false,
  error: error.code ?? 'Error desconocido',
});

const withAuthErrorHandling = async <T extends AuthResponse | { success: boolean; error?: string }>(
  action: () => Promise<T>,
): Promise<T> => {
  try {
    return await action();
  } catch (error: any) {
    return authError(error) as T;
  }
};

export const AuthService = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    return withAuthErrorHandling(async () => {
      const credential = await signInWithEmailAndPassword(auth, email, password);
      
      if (!credential.user.emailVerified) {
        await signOut(auth);
        return { success: false, error: 'auth/email-not-verified' };
      }

      return { success: true, user: mapFirebaseUser(credential.user) };
    });
  },

  register: async (username: string, email: string, password: string): Promise<AuthResponse> => {
    return withAuthErrorHandling(async () => {
      const credential = await createUserWithEmailAndPassword(auth, email, password);
      await updateProfile(credential.user, { displayName: username });
      await sendEmailVerification(credential.user);
      await signOut(auth);

      return { success: true, user: mapFirebaseUser(credential.user, username) };
    });
  },

  logout: async (): Promise<void> => {
    await signOut(auth);
  },

  resetPassword: async (email: string): Promise<{ success: boolean; error?: string }> => {
    return withAuthErrorHandling(async () => {
      await sendPasswordResetEmail(auth, email);
      return { success: true };
    });
  },

  onAuthChange: (callback: (user: User | null) => void): Unsubscribe => {
    return onAuthStateChanged(auth, (fbUser) => {
      callback(fbUser ? mapFirebaseUser(fbUser) : null);
    });
  },

  onBootstrapAuthChange: (callback: (isAllowed: boolean, hasUser: boolean) => void | Promise<void>): Unsubscribe => {
    return onAuthStateChanged(auth, (fbUser) => {
      callback(!!fbUser && (fbUser.isAnonymous || fbUser.emailVerified), !!fbUser);
    });
  },

  loginWithGoogle: async (idToken: string): Promise<AuthResponse> => {
    return withAuthErrorHandling(async () => {
      const credential = GoogleAuthProvider.credential(idToken);
      const userCredential = await signInWithCredential(auth, credential);
      return { success: true, user: mapFirebaseUser(userCredential.user) };
    });
  },

  loginAnonymously: async (): Promise<AuthResponse> => {
    return withAuthErrorHandling(async () => {
      const credential = await signInAnonymously(auth);
      return { success: true, user: mapFirebaseUser(credential.user) };
    });
  },

  updateUserName: async (newName: string): Promise<AuthResponse> => {
    return withAuthErrorHandling(async () => {
      if (!auth.currentUser) throw new Error('No user logged in');
      await updateProfile(auth.currentUser, { displayName: newName });

      return { success: true, user: mapFirebaseUser(auth.currentUser, newName) };
    });
  },

  deleteAccount: async (): Promise<{ success: boolean; error?: string }> => {
    return withAuthErrorHandling(async () => {
      if (!auth.currentUser) throw new Error('No user logged in');
      await deleteUser(auth.currentUser);
      return { success: true };
    });
  },

  getCurrentUser: (): User | null => {
    return auth.currentUser ? mapFirebaseUser(auth.currentUser) : null;
  },
};
