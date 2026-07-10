export const queryKeys = {
  user: (userId: string) => ["user", userId] as const,
  resources: (userId: string, courseName: string) =>
    ["resources", userId, courseName] as const,
}
