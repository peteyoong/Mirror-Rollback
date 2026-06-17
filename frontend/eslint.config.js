// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  expoConfig,
  {
    ignores: ['dist/*', 'web_dist/*', 'node_modules/*', '.expo/*'],
  },
  {
    // PFS-2.4 — recurring lint noise on .tsx files.  The recurring
    // failures observed across 18+ forks were almost exclusively
    // stylistic rules (apostrophes in JSX text, Array<T> vs T[]
    // preference) — they don't catch real bugs, they just turn lint
    // into red wallpaper.  Downgrade or disable the worst offenders
    // here so `yarn lint` returns useful signal again.
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx'],
    rules: {
      // Apostrophes / quotes inside JSX text are LEGAL HTML and read
      // by every modern browser exactly as authored.  Escaping them
      // ("you're" → "you&apos;re") makes the source unreadable and
      // doesn't change rendering.  Off.
      'react/no-unescaped-entities': 'off',

      // Array<T> vs T[] is a stylistic preference, not a defect.
      // Demote from warning to off so the noise doesn't drown out
      // real findings.
      '@typescript-eslint/array-type': 'off',

      // react-hooks/exhaustive-deps is genuinely useful but produces
      // false-positives for stable refs (Animated.Value, setters,
      // toast helpers).  Keep as warn (not error) so legit deps
      // bugs are still surfaced without blocking the build.
      'react-hooks/exhaustive-deps': 'warn',

      // Unused vars during refactor / scaffolding: warn, never error,
      // and tolerate the leading-underscore prefix convention.
      '@typescript-eslint/no-unused-vars': ['warn', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_',
        ignoreRestSiblings: true,
      }],
      'no-unused-vars': 'off', // delegated to the TS variant above
    },
  },
]);
