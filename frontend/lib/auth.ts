"use client";

import type { LoginResponse, User } from "@/types/api";

const ACCESS_KEY = "converra.access_token";
const REFRESH_KEY = "converra.refresh_token";
const USER_KEY = "converra.user";

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_KEY);
}

export function saveSession(tokens: LoginResponse, user?: User) {
  window.localStorage.setItem(ACCESS_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  if (user) {
    window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function saveUser(user: User) {
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(USER_KEY);
  return value ? (JSON.parse(value) as User) : null;
}

export function clearSession() {
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
  window.localStorage.removeItem(USER_KEY);
}
