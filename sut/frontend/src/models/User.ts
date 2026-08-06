export interface User {
  uid: string;
  displayName?: string;
  email: string;
  isAnonymous: boolean;
}

export interface AuthResponse {
  success: boolean;
  token?: string;
  user?: User;
  error?: string;
}
