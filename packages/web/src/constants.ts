import { DurationEnum } from "@/api/generated/endpoints";

export const DURATION_OPTIONS = [
  { value: "1 hour", label: "1 hour" },
  { value: "12 hours", label: "12 hours" },
  { value: "24 hours", label: "24 hours" },
  { value: "48 hours", label: "48 hours" },
  { value: "3 days", label: "3 days" },
  { value: "4 days", label: "4 days" },
  { value: "1 week", label: "1 week" },
  { value: "2 weeks", label: "2 weeks" },
] as const;

export const DURATION_ENUM_VALUES = [
  "1 hour",
  "12 hours",
  "24 hours",
  "48 hours",
  "3 days",
  "4 days",
  "1 week",
  "2 weeks",
] as const;

export const FREQUENCY_OPTIONS = [
  { value: "hourly", label: "Hourly" },
  { value: "daily", label: "Daily" },
  { value: "every_2_days", label: "Every 2 days" },
  { value: "weekly", label: "Weekly" },
] as const;

export const TIMEZONE_OPTIONS = [
  { value: "America/New_York", label: "Eastern Time (US)" },
  { value: "America/Chicago", label: "Central Time (US)" },
  { value: "America/Denver", label: "Mountain Time (US)" },
  { value: "America/Los_Angeles", label: "Pacific Time (US)" },
  { value: "America/Anchorage", label: "Alaska Time" },
  { value: "Pacific/Honolulu", label: "Hawaii Time" },
  { value: "Europe/London", label: "London (GMT/BST)" },
  { value: "Europe/Dublin", label: "Dublin (GMT/BST)" },
  { value: "Europe/Paris", label: "Central European Time" },
  { value: "Europe/Berlin", label: "Berlin (CET)" },
  { value: "Europe/Moscow", label: "Moscow Time" },
  { value: "Asia/Tokyo", label: "Japan Time" },
  { value: "Asia/Shanghai", label: "China Time" },
  { value: "Asia/Kolkata", label: "India Time" },
  { value: "Australia/Sydney", label: "Sydney Time" },
  { value: "UTC", label: "UTC" },
] as const;

export const NMR_EXTENSION_OPTIONS = [
  { value: "0", label: "None" },
  { value: "1", label: "1 per player" },
  { value: "2", label: "2 per player" },
] as const;

export const EXTEND_DURATION_OPTIONS = [
  { value: DurationEnum["1_hour"], label: "1 hour" },
  { value: DurationEnum["12_hours"], label: "12 hours" },
  { value: DurationEnum["24_hours"], label: "24 hours" },
  { value: DurationEnum["48_hours"], label: "48 hours" },
  { value: DurationEnum["3_days"], label: "3 days" },
  { value: DurationEnum["4_days"], label: "4 days" },
  { value: DurationEnum["1_week"], label: "1 week" },
  { value: DurationEnum["2_weeks"], label: "2 weeks" },
] as const;
