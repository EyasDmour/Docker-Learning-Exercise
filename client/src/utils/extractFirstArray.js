export const extractFirstArray = (data) => {
  if (!data || typeof data !== "object") {
    return null;
  }

  for (const value of Object.values(data)) {
    if (Array.isArray(value)) {
      return value;
    }

    if (value && typeof value === "object") {
      const nested = extractFirstArray(value);
      if (nested) {
        return nested;
      }
    }
  }

  return null;
};
