module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
  },
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'prettier', 'import', 'react', 'jsx-a11y'],
  settings: {
    react: {
      version: 'detect',
    },
    'import/resolver': {
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
        moduleDirectory: ['node_modules', 'src/'],
      },
    },
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'plugin:prettier/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  rules: {
    'import/no-named-as-default-member': 'off',
    'import/no-mutable-exports': 'warn',
    'import/prefer-default-export': 'warn',
    'import/extensions': 'warn',
    'import/order': [
      'warn',
      {
        groups: ['builtin', 'external', 'internal'],
        pathGroups: [
          {
            pattern: 'react',
            group: 'external',
            position: 'before',
          },
        ],
        pathGroupsExcludedImportTypes: ['react'],
        'newlines-between': 'always',
      },
    ],
    '@typescript-eslint/indent': 'off',
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        ignoreRestSiblings: true,
        varsIgnorePattern: '^_',
        argsIgnorePattern: '^_',
      },
    ],
    'max-len': ['warn', { code: 120, ignoreUrls: true, ignoreStrings: true, ignoreTemplateLiterals: true }],
    'react/display-name': 'off',
    'react/prop-types': 'off',
    'react/destructuring-assignment': 'off',
    'react/no-unused-prop-types': 'off',
    'react/forbid-prop-types': 'off',
    'react/jsx-indent': ['warn', 2],
    'react/jsx-indent-props': ['warn', 2],
    'react/jsx-props-no-spreading': [
      'warn',
      {
        explicitSpread: 'ignore',
      },
    ],
    'prettier/prettier': [
      'warn',
      {
        singleQuote: true,
        endOfLine: 'auto',
        jsxSingleQuote: true,
      },
    ],
  },
};
