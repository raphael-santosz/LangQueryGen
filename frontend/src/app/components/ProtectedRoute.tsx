'use client';

import { useAuth } from '../../context/AuthContext';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      // Redireciona para a página de login, mantendo o idioma atual
      const locale = pathname.split('/')[1]; // Extrai o idioma da URL (ex.: "en" ou "pt")
      router.push(`/${locale}/login`);
    }
  }, [user, loading, router, pathname]);

  if (loading) {
    return <div>Loading...</div>; // Pode personalizar com um componente de loading
  }

  return user ? <>{children}</> : null;
}