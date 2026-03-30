import { useTheme } from "../../app/theme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const nextThemeLabel = theme === "light" ? "dark" : "light";

  return (
    <button
      aria-label={`Switch to ${nextThemeLabel} theme`}
      className="theme-toggle"
      onClick={toggleTheme}
      type="button"
    >
      <span className="theme-toggle__icon" aria-hidden="true">
        {theme === "light" ? "◐" : "◑"}
      </span>
    </button>
  );
}
