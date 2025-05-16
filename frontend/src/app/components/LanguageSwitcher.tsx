"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter, usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { Globe } from "lucide-react";
import { routing } from "@/i18n/routing";

// Lista de idiomas disponíveis
const locales = routing.locales; // ["en", "pt", "es", etc.]

// Variantes de animação para o dropdown
const dropdownVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.2 } },
  exit: { opacity: 0, y: 10, transition: { duration: 0.2 } },
};

export default function LanguageSwitcher() {
  const t = useTranslations("LanguageSwitcher");
  const currentLocale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  // Fechar o dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!(event.target as HTMLElement).closest(".language-switcher")) {
        setIsOpen(false);
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  // Função para mudar o idioma
  const changeLanguage = (locale: string) => {
    const newPath = pathname.replace(/^\/[^\/]+/, `/${locale}`);
    router.push(newPath);
    setIsOpen(false);
  };

  // Mapa de nomes de idiomas e bandeiras
  const languageInfo: Record<string, { name: string; flag: string }> = {
    en: { name: t("english"), flag: "/Flags/flag-icons-main/flags/4x3/gb.svg" },
    pt: { name: t("portuguese"), flag: "/Flags/flag-icons-main/flags/4x3/br.svg" },
    es: { name: t("spanish"), flag: "/Flags/flag-icons-main/flags/4x3/es.svg" },
  };

  return (
    <div className="language-switcher fixed bottom-6 right-6 md:bottom-3 md:right-8 z-50">
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-3 rounded-full shadow-lg bg-black text-white hover:bg-slate-600 transition-colors duration-200"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        aria-label={t("toggleLanguageMenu")}
        title={t("toggleLanguageMenu")}
      >
        <Globe size={24} />
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.ul
            className="absolute bottom-14 right-0 bg-black text-white rounded-lg shadow-lg p-2 w-48"
            variants={dropdownVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {locales.map((locale) => (
              <li key={locale}>
                <button
                  onClick={() => changeLanguage(locale)}
                  className={`flex items-center gap-3 w-full text-left px-4 py-2 rounded-md hover:bg-slate-700 transition-colors ${
                    locale === currentLocale ? "bg-slate-600" : ""
                  }`}
                  aria-current={locale === currentLocale ? "true" : "false"}
                >
                  <Image
                    src={languageInfo[locale]?.flag}
                    alt={`${languageInfo[locale]?.name} flag`}
                    width={24}
                    height={24}
                    className="rounded-sm"
                  />
                  {languageInfo[locale]?.name}
                </button>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}