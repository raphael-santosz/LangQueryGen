// app/[locale]/layout.tsx
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { AuthProvider } from "@/context/AuthContext";
import { getMessages } from "next-intl/server";
import "../../app/globals.css";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  const messages = await getMessages({ locale });

  return (
    <html lang={locale} className="h-full">
      <body className="h-full">
        <NextIntlClientProvider locale={locale} messages={messages}>
            <AuthProvider>
              {children}
              <LanguageSwitcher />
            </AuthProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}