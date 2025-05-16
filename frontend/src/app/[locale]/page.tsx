// app/page.tsx
import { redirect } from 'next/navigation';

export default function Home() {
  redirect('/en/login'); // Redireciona para /en/login
  return null; // Não renderiza nada, pois será redirecionado
}