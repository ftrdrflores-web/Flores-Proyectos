import useThemeStore from '@store/themeStore'

const useTheme = () => {
  const isDark      = useThemeStore((s) => s.isDark)
  const toggleTheme = useThemeStore((s) => s.toggleTheme)
  return { isDark, toggleTheme }
}

export default useTheme