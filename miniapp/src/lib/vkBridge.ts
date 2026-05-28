import bridge from "@vkontakte/vk-bridge";

/**
 * Returns raw launch_params query string for backend signature validation.
 * In browser dev (outside VK) returns a mock string if VITE_MOCK_LAUNCH_PARAMS=true.
 */
export async function getLaunchParams(): Promise<string> {
  const isInsideVK = typeof window !== "undefined" && window.location.search.includes("vk_user_id");

  if (isInsideVK) {
    return window.location.search.replace(/^\?/, "");
  }

  if (import.meta.env.VITE_MOCK_LAUNCH_PARAMS === "true") {
    // Dev-only mock. Backend MUST reject this in production
    // (settings.vk_app_secure_key check enforces that).
    return "vk_user_id=1&vk_app_id=0&vk_is_app_user=1&sign=mock";
  }

  // Fallback for stricter environments — attempt to query the bridge directly.
  try {
    const result = await bridge.send("VKWebAppGetLaunchParams");
    return new URLSearchParams(result as unknown as Record<string, string>).toString();
  } catch {
    throw new Error("Cannot obtain VK launch_params — are we inside VK?");
  }
}
