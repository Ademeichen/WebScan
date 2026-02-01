export const lightTheme = {
  name: 'light',
  colors: {
    primary: '#6366f1',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#3b82f6'
  }
}

export const darkTheme = {
  name: 'dark',
  colors: {
    primary: '#818cf8',
    success: '#34d399',
    warning: '#fbbf24',
    danger: '#f87171',
    info: '#60a5fa'
  }
}

export const themes = {
  light: lightTheme,
  dark: darkTheme
}

export const useTheme = () => {
  const getTheme = (themeName) => {
    return themes[themeName] || lightTheme
  }

  const setTheme = (themeName) => {
    const theme = getTheme(themeName)
    document.documentElement.setAttribute('data-theme', theme.name)
    localStorage.setItem('theme', themeName)
  }

  const getCurrentTheme = () => {
    return localStorage.getItem('theme') || 'light'
  }

  const initTheme = () => {
    const themeName = getCurrentTheme()
    setTheme(themeName)
  }

  return {
    getTheme,
    setTheme,
    getCurrentTheme,
    initTheme
  }
}