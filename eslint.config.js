import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      // Hydration and timer effects intentionally synchronize React state with
      // IndexedDB and browser clocks. The rule is too strict for those effects.
      'react-hooks/set-state-in-effect': 'off',
      // shadcn/ui exports variant helpers next to components by design.
      'react-refresh/only-export-components': 'off',
    },
  },
])
