import "./globals.css";

export const metadata = {
  title: "Immortal Eye - AI powered Elder Abuse Monitor",
  description: "Get a 24/7 elder caretaker.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
