export const lightTheme = {
  name: 'light',
  colors: {
    primary: '#409EFF',
    success: '#67C23A',
    warning: '#E6A23C',
    danger: '#F56C6C',
    info: '#909399'
  }
}

export const darkTheme = {
  name: 'dark',
  colors: {
    primary: '#409EFF',
    success: '#67C23A',
    warning: '#E6A23C',
    danger: '#F56C6C',
    info: '#909399'
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