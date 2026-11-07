# Bundled UI fonts

Inter and Noto Sans Arabic are vendored as `.woff2` files so production builds
do not depend on Google Fonts at compile time (required for offline CI and
restricted networks).

Sources: [Fontsource](https://fontsource.org/) packages `@fontsource/inter`
and `@fontsource/noto-sans-arabic` (SIL Open Font License 1.1). Loaded via
`next/font/local` in `src/lib/fonts.ts`.
