import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'

export default [
  js.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  {
    files: ['**/*.{js,mjs,cjs,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        console: 'readonly',
        window: 'readonly',
        document: 'readonly',
        localStorage: 'readonly',
        navigator: 'readonly'
      }
    },
    rules: {
      'vue/multi-word-component-names': 'off'
    }
  },
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      '*.config.js'
    ]
  }
]
