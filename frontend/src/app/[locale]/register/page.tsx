"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { createUserWithEmailAndPassword, updateProfile } from "firebase/auth";
import { auth, db } from "@/lib/firebase";
import { doc, setDoc } from "firebase/firestore";
import { useLocale, useTranslations } from "next-intl";
import { Lock, Eye, EyeOff } from "lucide-react";
import sodium from "libsodium-wrappers";

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

export default function RegisterPage() {
  const router = useRouter();
  const t = useTranslations();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    position: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [firebaseError, setFirebaseError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const locale = useLocale();
  const [sodiumReady, setSodiumReady] = useState(false);

  // Inicializa o sodium
  useEffect(() => {
    const initSodium = async () => {
      await sodium.ready;
      setSodiumReady(true);
    };
    initSodium();
  }, []);

  const handleChange = (e: { target: { name: any; value: any } }) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const validateForm = () => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = t("Register.errors.nameRequired");
    }

    if (!formData.email) {
      newErrors.email = t("Register.errors.emailRequired");
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = t("Register.errors.emailInvalid");
    }

    if (!formData.password) {
      newErrors.password = t("Register.errors.passwordRequired");
    } else if (formData.password.length < 6) {
      newErrors.password = t("Register.errors.passwordTooShort");
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = t("Register.errors.confirmPasswordRequired");
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = t("Register.errors.passwordsDoNotMatch");
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    setFirebaseError("");
    setSuccessMessage("");

    if (!sodiumReady) {
      setFirebaseError(t("Register.errors.sodiumNotReady"));
      return;
    }

    if (validateForm()) {
      setIsLoading(true);
      try {
        const userCredential = await createUserWithEmailAndPassword(
          auth,
          formData.email,
          formData.password
        );
        await updateProfile(userCredential.user, { displayName: formData.name });

        const messageToEncrypt = "funcionario";
        const keyBase64 = "q9egeDk+L1t2C8pgH/9rzE/ezPflr3cx6JLujZSiaX8=";
        const key = sodium.from_base64(keyBase64, sodium.base64_variants.ORIGINAL);
        const nonce = sodium.randombytes_buf(sodium.crypto_secretbox_NONCEBYTES);

        const encryptedMessage = sodium.crypto_secretbox_easy(
          sodium.from_string(messageToEncrypt),
          nonce,
          key
        );
        const fullMessage = new Uint8Array([...nonce, ...encryptedMessage]);
        const encryptedMessageBase64 = sodium.to_base64(
          fullMessage,
          sodium.base64_variants.ORIGINAL
        );

        if (userCredential.user) {
          await setDoc(doc(db, "Users", userCredential.user.uid), {
            name: formData.name,
            email: formData.email,
            position: "Funcionário",
            tokenKey: encryptedMessageBase64.toString(),
            termsAccepted: true,
          });
          setSuccessMessage(t("Register.successMessage"));
          setIsLoading(false);

          setTimeout(() => {
            router.push(`/${locale}/login`);
          }, 3000);
        }
      } catch (error: unknown) {
        let message = t("Register.errors.unknownError");

        if (error && typeof error === "object" && "code" in error) {
          const firebaseCode = (error as { code: string }).code;
          switch (firebaseCode) {
            case "auth/email-already-in-use":
              message = t("Register.errors.emailAlreadyInUse");
              break;
            case "auth/invalid-email":
              message = t("Register.errors.emailInvalid");
              break;
            case "auth/weak-password":
              message = t("Register.errors.weakPassword");
              break;
            case "auth/operation-not-allowed":
              message = t("Register.errors.operationNotAllowed");
              break;
            default:
              message = t("Register.errors.defaultError");
          }
        }

        setFirebaseError(message);
        setIsLoading(false);
      } finally {
        setIsLoading(false);
      }
    }
  };

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
  };

  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5, ease: "easeOut" },
    },
  };

  const buttonVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5, delay: 0.8 },
    },
    hover: { scale: 1.03, transition: { duration: 0.2 } },
    tap: { scale: 0.97 },
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <motion.div
        className="relative flex flex-col md:flex-row w-full max-w-4xl mx-4 bg-white rounded-xl shadow-lg overflow-hidden"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Left Section: Image */}
        <motion.div
          className="w-full md:w-1/2 h-64 md:h-auto bg-no-repeat bg-contain bg-center relative order-first md:order-last"
          style={{
            backgroundImage: "url('/register-page.png')",
            marginRight: "15px", // Adiciona um deslocamento à direita
          }}
          initial={{ opacity: 0, x: 70 }} // Ajusta o ponto inicial da animação (mais à direita)
          animate={{ opacity: 1, x: 20 }} // Ajusta o ponto final da animação
          transition={{ duration: 1.2 }}
        >
          {/* Conteúdo adicional, se houver */}
        </motion.div>

        {/* Right Section: Form */}
        <div className="w-full md:w-1/2 p-8 order-last">
          <motion.h1
            className="text-3xl font-bold text-gray-900 mb-8"
            variants={itemVariants}
          >
            {t("Register.title")}
          </motion.h1>

          {firebaseError && (
            <motion.div
              className="mb-6 p-3 bg-red-100 text-red-600 rounded-lg text-center text-sm"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {firebaseError}
            </motion.div>
          )}

          {successMessage && (
            <motion.div
              className="mb-6 p-3 bg-green-100 text-green-700 rounded-lg text-center text-sm"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {successMessage}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <motion.div variants={itemVariants} className="space-y-2">
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                {t("Register.fullName")}
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`w-full px-4 py-3 border ${
                  errors.name ? "border-red-300" : "border-gray-300"
                } rounded-lg focus:outline-none focus:ring-1 focus:ring-black text-gray-900 transition duration-200`}
                placeholder={t("Register.fullNamePlaceholder")}
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            </motion.div>

            <motion.div variants={itemVariants} className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                {t("Register.email")}
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`w-full px-4 py-3 border ${
                  errors.email ? "border-red-300" : "border-gray-300"
                } rounded-lg focus:outline-none focus:ring-1 focus:ring-black text-gray-900 transition duration-200`}
                placeholder={t("Register.emailPlaceholder")}
              />
              {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
            </motion.div>

            <motion.div variants={itemVariants} className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                {t("Register.password")}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 border ${
                    errors.password ? "border-red-300" : "border-gray-300"
                  } rounded-lg focus:outline-none focus:ring-1 focus:ring-black text-gray-900 transition duration-200`}
                  placeholder={t("Register.passwordPlaceholder")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-900 transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.password && <p className="mt-1 text-sm text-red-600">{errors.password}</p>}
            </motion.div>

            <motion.div variants={itemVariants} className="space-y-2">
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                {t("Register.confirmPassword")}
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 border ${
                    errors.confirmPassword ? "border-red-300" : "border-gray-300"
                  } rounded-lg focus:outline-none focus:ring-1 focus:ring-black text-gray-900 transition duration-200`}
                  placeholder={t("Register.confirmPasswordPlaceholder")}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-900 transition-colors"
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.confirmPassword && <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>}
            </motion.div>

            <motion.button
              type="submit"
              disabled={isLoading || !sodiumReady}
              className="w-full bg-black text-white py-3 rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-1 focus:ring-black transition duration-200 font-medium flex items-center justify-center"
              variants={buttonVariants}
              initial="hidden"
              animate="visible"
              whileHover="hover"
              whileTap="tap"
            >
              {isLoading ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  {t("Register.buttons.creatingAccount")}
                </>
              ) : (
                t("Register.signUp")
              )}
            </motion.button>
          </form>

          <motion.div
            className="mt-6 text-center text-sm text-gray-600"
            variants={itemVariants}
          >
            {t("Register.alreadyHaveAccount")}{" "}
            <Link
              href={`/${locale}/login`}
              className="text-blue-600 hover:text-blue-500 transition-colors"
            >
              {t("Register.signIn")}
            </Link>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}

