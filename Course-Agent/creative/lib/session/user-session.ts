const USER_ID_KEY = "zhixue_user_id"

export const getUserId = () => {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(USER_ID_KEY)
}

export const setUserId = (value: string) => {
  const userId = value.trim()
  if (!userId) throw new Error("user_id is required")
  window.localStorage.setItem(USER_ID_KEY, userId)
}

export const clearUserId = () => window.localStorage.removeItem(USER_ID_KEY)
