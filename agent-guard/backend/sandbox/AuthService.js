/**
 * Authentication Service Module
 */
export async function loginUser(credentials) {
  if (!credentials.email || !credentials.password) {
    throw new Error("Missing email or password");
  }
  // Simulated authentication check
  return { token: "sample-jwt-token-12345", user: { email: credentials.email } };
}
