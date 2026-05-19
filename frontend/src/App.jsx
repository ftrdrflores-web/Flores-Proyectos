import { RouterProvider } from 'react-router-dom'
import { Toaster } from 'sileo'
import { useEffect } from 'react'
import router from './router'
import useThemeStore from '@store/themeStore'

const App = () => {
  const initTheme = useThemeStore((s) => s.initTheme)

  useEffect(() => {
    initTheme()
  }, [initTheme])

  return (
    <>
      <RouterProvider router={router} />
      <Toaster position="top-right" />
    </>
  )
}

export default App