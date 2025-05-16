"use client"

import type React from "react"
import { useState } from "react"
import { useTranslations, useLocale } from "next-intl"
import { signInWithEmailAndPassword, type AuthError } from "firebase/auth"
import { auth, db } from "@/lib/firebase"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Eye, EyeOff } from "lucide-react"
import Link from "next/link"
import { doc, getDoc } from "firebase/firestore"

export default function LoginPage() {
  const t = useTranslations()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const router = useRouter()
  const locale = useLocale()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;

      // Consulta ao Firestore para obter a posição do usuário
      const userDoc = await getDoc(doc(db, 'Users', user.uid));
      if (userDoc.exists()) {
        const userData = userDoc.data();
        const userPosition = userData.position;

        // Validação do locale
        const validLocales = ['en', 'pt', 'es'];
        const targetLocale = validLocales.includes(locale) ? locale : 'en';

        // Navegação condicional com base na posição
        if (userPosition === 'Main-admin' || userPosition === 'Gestor') {
          router.push(`/${targetLocale}/dashboard`);
        } else {
          router.push(`/${targetLocale}/chat`);
        }
      } else {
        setError(t('Login.userDataNotFound'));
      }
    } catch (err) {
      const authError = err as AuthError;
      switch (authError.code) {
        case 'auth/wrong-password':
          setError(t('Login.wrongPassword'));
          break;
        case 'auth/user-not-found':
          setError(t('Login.userNotFound'));
          break;
        case 'auth/invalid-email':
          setError(t('Login.invalidEmail'));
          break;
        case 'auth/too-many-requests':
          setError(t('Login.tooManyRequests'));
          break;
        default:
          setError(t('Login.genericError'));
      }
    }
  }

  // Variants for animations
  const containerVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.8,
        when: "beforeChildren",
        staggerChildren: 0.2,
      },
    },
  }

  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5, ease: "easeOut" },
    },
  }

  const buttonVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5, delay: 0.8 },
    },
    hover: {
      scale: 1.03,
      transition: { duration: 0.2 },
    },
    tap: { scale: 0.97 },
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <motion.div
        className="relative flex flex-col md:flex-row w-full max-w-4xl mx-4 bg-white rounded-xl shadow-lg overflow-hidden"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Right Section: Image and Text */}
        <motion.div
          className="w-full md:w-1/2 h-64 md:h-auto bg-no-repeat bg-contain bg-center relative order-first md:order-last"
          style={{
            backgroundImage: "url('/login-page.png')",
          }}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1.2 }}
        >
          {/* Conteúdo adicional, se houver */}
        </motion.div>

        {/* Left Section: Form */}
        <div className="w-full md:w-1/2 p-8 order-last md:order-first">
          <motion.h1
            className="text-3xl font-bold text-gray-900 mb-8"
            variants={itemVariants}
          >
            {t("Login.title", { defaultMessage: "Welcome back!" })}
          </motion.h1>

          {error && (
            <motion.div
              className="mb-6 p-3 bg-red-100 text-red-600 rounded-lg text-center text-sm"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            <motion.div variants={itemVariants}>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t("Login.email", { defaultMessage: "Email" })}
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-black text-gray-900 transition duration-200"
                placeholder={t("Login.emailPlaceholder", { defaultMessage: "Enter your email address" })}
              />
            </motion.div>

            <motion.div variants={itemVariants}>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  {t("Login.password", { defaultMessage: "Password" })}
                </label>
                <Link
                  href={`/${locale}/forgot-password`}
                  className="text-xs text-black-600 hover:text-gray-600 transition-colors"
                >
                  {t("Login.forgotPassword", { defaultMessage: "Forgot password?" })}
                </Link>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-black text-gray-900 transition duration-200"
                  placeholder={t("Login.passwordPlaceholder", { defaultMessage: "Enter your password" })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-900 transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </motion.div>

            <motion.button
              type="submit"
              className="w-full bg-black text-white py-3 rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200 font-medium"
              variants={buttonVariants}
              initial="hidden"
              animate="visible"
              whileHover="hover"
              whileTap="tap"
            >
              {t("Login.submit", { defaultMessage: "Login" })}
            </motion.button>
          </form>

          {/* Create Account Link */}
          <motion.div
            className="mt-6 text-center text-sm text-gray-600"
            variants={itemVariants}
          >
            {t("Login.noAccount", { defaultMessage: "Don't have an account?" })}{" "}
            <Link
              href={`/${locale}/register`}
              className="text-blue-600 hover:text-black-500 transition-colors"
            >
              {t("Login.register", { defaultMessage: "Create account" })}
            </Link>
          </motion.div>
        </div>
      </motion.div>
    </div>
  )
}