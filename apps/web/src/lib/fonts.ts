import localFont from "next/font/local";

export const fontSans = localFont({
  src: [
    {
      path: "../assets/fonts/inter/inter-latin-400-normal.woff2",
      weight: "400",
      style: "normal",
    },
    {
      path: "../assets/fonts/inter/inter-latin-500-normal.woff2",
      weight: "500",
      style: "normal",
    },
    {
      path: "../assets/fonts/inter/inter-latin-600-normal.woff2",
      weight: "600",
      style: "normal",
    },
    {
      path: "../assets/fonts/inter/inter-latin-700-normal.woff2",
      weight: "700",
      style: "normal",
    },
  ],
  display: "swap",
  variable: "--font-sans",
});

export const fontArabic = localFont({
  src: [
    {
      path: "../assets/fonts/noto-sans-arabic/noto-sans-arabic-arabic-400-normal.woff2",
      weight: "400",
      style: "normal",
    },
    {
      path: "../assets/fonts/noto-sans-arabic/noto-sans-arabic-arabic-500-normal.woff2",
      weight: "500",
      style: "normal",
    },
    {
      path: "../assets/fonts/noto-sans-arabic/noto-sans-arabic-arabic-600-normal.woff2",
      weight: "600",
      style: "normal",
    },
    {
      path: "../assets/fonts/noto-sans-arabic/noto-sans-arabic-arabic-700-normal.woff2",
      weight: "700",
      style: "normal",
    },
  ],
  display: "swap",
  variable: "--font-arabic",
});
