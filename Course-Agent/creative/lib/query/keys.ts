export const queryKeys = {
  user: (userId: string) => ["user", userId] as const,
  resources: (userId: string, courseName: string) =>
    ["resources", userId, courseName] as const,
  path: (userId: string, courseName: string) =>
    ["path", userId, courseName] as const,
  evaluation: (userId: string, courseName: string) =>
    ["evaluation", userId, courseName] as const,
}
