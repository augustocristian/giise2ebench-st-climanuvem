const mockSignInWithEmailAndPassword = jest.fn();
const mockCreateUserWithEmailAndPassword = jest.fn();
const mockSendEmailVerification = jest.fn();
const mockSendPasswordResetEmail = jest.fn();
const mockSignOut = jest.fn();
const mockOnAuthStateChanged = jest.fn();
const mockUpdateProfile = jest.fn();
const mockDeleteUser = jest.fn();
const mockCredential = jest.fn();
const mockSignInWithCredential = jest.fn();
const mockSignInAnonymously = jest.fn();

const authMock = {
  currentUser: null as any,
};

const firebaseAuthMock = {
  __esModule: true,
  signInWithEmailAndPassword: mockSignInWithEmailAndPassword,
  createUserWithEmailAndPassword: mockCreateUserWithEmailAndPassword,
  sendEmailVerification: mockSendEmailVerification,
  sendPasswordResetEmail: mockSendPasswordResetEmail,
  signOut: mockSignOut,
  onAuthStateChanged: mockOnAuthStateChanged,
  updateProfile: mockUpdateProfile,
  deleteUser: mockDeleteUser,
  GoogleAuthProvider: { credential: mockCredential },
  signInWithCredential: mockSignInWithCredential,
  signInAnonymously: mockSignInAnonymously,
};

const loadAuthService = () => {
  jest.resetModules();
  jest.doMock('firebase/auth', () => firebaseAuthMock);
  jest.doMock('@/src/config/firebaseConfig', () => ({
    __esModule: true,
    auth: authMock,
  }));
  return require('@/src/services/AuthService').AuthService;
};

const firebaseUser = {
  uid: 'uid-1',
  displayName: 'User One',
  email: 'user@example.com',
  isAnonymous: false,
  emailVerified: true,
};

describe('AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    authMock.currentUser = null;
  });

  it('logs in verified users', async () => {
    mockSignInWithEmailAndPassword.mockResolvedValue({ user: firebaseUser });
    const AuthService = loadAuthService();

    await expect(AuthService.login('user@example.com', 'secret')).resolves.toMatchObject({
      success: true,
      user: { uid: 'uid-1', displayName: 'User One', email: 'user@example.com', isAnonymous: false },
    });
  });

  it('signs out unverified users and returns an email verification error', async () => {
    mockSignInWithEmailAndPassword.mockResolvedValue({ user: { ...firebaseUser, emailVerified: false } });
    const AuthService = loadAuthService();

    await expect(AuthService.login('user@example.com', 'secret')).resolves.toEqual({
      success: false,
      error: 'auth/email-not-verified',
    });
    expect(mockSignOut).toHaveBeenCalledWith(authMock);
  });

  it('maps firebase login exceptions to auth responses', async () => {
    mockSignInWithEmailAndPassword.mockRejectedValue({ code: 'auth/wrong-password' });
    const AuthService = loadAuthService();

    await expect(AuthService.login('user@example.com', 'bad')).resolves.toEqual({
      success: false,
      error: 'auth/wrong-password',
    });
  });

  it('registers users and sends verification email', async () => {
    mockCreateUserWithEmailAndPassword.mockResolvedValue({ user: firebaseUser });
    const AuthService = loadAuthService();

    await expect(AuthService.register('Fresh User', 'fresh@example.com', 'secret')).resolves.toMatchObject({
      success: true,
      user: { displayName: 'Fresh User' },
    });
    expect(mockUpdateProfile).toHaveBeenCalledWith(firebaseUser, { displayName: 'Fresh User' });
    expect(mockSendEmailVerification).toHaveBeenCalledWith(firebaseUser);
    expect(mockSignOut).toHaveBeenCalledWith(authMock);
  });

  it('resets password', async () => {
    mockSendPasswordResetEmail.mockResolvedValue(undefined);
    const AuthService = loadAuthService();

    await expect(AuthService.resetPassword('user@example.com')).resolves.toEqual({ success: true });
  });

  it('subscribes to auth changes and maps firebase users', () => {
    const unsubscribe = jest.fn();
    mockOnAuthStateChanged.mockImplementation((_auth, callback) => {
      callback(firebaseUser);
      callback(null);
      return unsubscribe;
    });
    const AuthService = loadAuthService();
    const callback = jest.fn();

    expect(AuthService.onAuthChange(callback)).toBe(unsubscribe);
    expect(callback).toHaveBeenNthCalledWith(1, expect.objectContaining({ uid: 'uid-1' }));
    expect(callback).toHaveBeenNthCalledWith(2, null);
  });

  it('computes bootstrap auth state from verified and anonymous users', () => {
    mockOnAuthStateChanged.mockImplementation((_auth, callback) => {
      callback({ ...firebaseUser, emailVerified: true, isAnonymous: false });
      callback({ ...firebaseUser, emailVerified: false, isAnonymous: false });
      callback({ ...firebaseUser, emailVerified: false, isAnonymous: true });
      return jest.fn();
    });
    const AuthService = loadAuthService();
    const callback = jest.fn();

    AuthService.onBootstrapAuthChange(callback);

    expect(callback).toHaveBeenNthCalledWith(1, true, true);
    expect(callback).toHaveBeenNthCalledWith(2, false, true);
    expect(callback).toHaveBeenNthCalledWith(3, true, true);
  });

  it('logs in with Google credentials and anonymously', async () => {
    mockCredential.mockReturnValue('google-credential');
    mockSignInWithCredential.mockResolvedValue({ user: firebaseUser });
    mockSignInAnonymously.mockResolvedValue({ user: { ...firebaseUser, isAnonymous: true } });
    const AuthService = loadAuthService();

    await expect(AuthService.loginWithGoogle('id-token')).resolves.toMatchObject({ success: true });
    await expect(AuthService.loginAnonymously()).resolves.toMatchObject({ success: true, user: { isAnonymous: true } });
    expect(mockCredential).toHaveBeenCalledWith('id-token');
  });

  it('updates and deletes the current account', async () => {
    authMock.currentUser = firebaseUser;
    const AuthService = loadAuthService();

    await expect(AuthService.updateUserName('New Name')).resolves.toMatchObject({
      success: true,
      user: { displayName: 'New Name' },
    });
    await expect(AuthService.deleteAccount()).resolves.toEqual({ success: true });
    expect(mockUpdateProfile).toHaveBeenCalledWith(firebaseUser, { displayName: 'New Name' });
    expect(mockDeleteUser).toHaveBeenCalledWith(firebaseUser);
  });

  it('returns errors when account mutations have no current user', async () => {
    const AuthService = loadAuthService();

    await expect(AuthService.updateUserName('New Name')).resolves.toMatchObject({ success: false });
    await expect(AuthService.deleteAccount()).resolves.toMatchObject({ success: false });
  });

  it('returns the mapped current user', () => {
    authMock.currentUser = firebaseUser;
    const AuthService = loadAuthService();

    expect(AuthService.getCurrentUser()).toMatchObject({ uid: 'uid-1' });
  });
});
