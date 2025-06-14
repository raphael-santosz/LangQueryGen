'use client';

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter, useSearchParams } from 'next/navigation';
import { signOut } from 'firebase/auth';
import { collection, getDocs, updateDoc, doc } from 'firebase/firestore';
import { auth, db } from '@/lib/firebase';
import { useAuth } from '@/context/AuthContext';
import {
  UsersIcon,
  LogOutIcon,
  MoreVerticalIcon,
  CheckIcon,
  ArrowRightFromLineIcon,
  SearchIcon,
} from 'lucide-react';
import type { LucideProps } from 'lucide-react';

interface User {
  id: string;
  name: string;
  email: string;
  position: string;
  tokenKey?: string;
}

interface MenuItemProps {
  icon: React.ComponentType<LucideProps>;
  text: string;
  isActive: boolean;
  onClick: () => void;
}

const MenuItem: React.FC<MenuItemProps> = ({ icon: Icon, text, isActive, onClick }) => (
  <li
    className={`flex items-center space-x-2 px-4 py-2 rounded-lg cursor-pointer ${
      isActive ? 'bg-black text-white' : 'text-gray-700 hover:bg-gray-200'
    }`}
    onClick={onClick}
  >
    <Icon className="h-5 w-5" />
    <span>{text}</span>
  </li>
);

export default function DashboardPage() {
  const t = useTranslations();
  const router = useRouter();
  const locale = useLocale();
  const searchParams = useSearchParams();
  const { user, loading } = useAuth();

  const [activeItem, setActiveItem] = useState(t('Users'));
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchPosition, setSearchPosition] = useState('');
  const [initialFilter, setInitialFilter] = useState('Todos');

  const email = searchParams.get('email') || user?.email || '';
  const token = searchParams.get('tokenCrypt') || '';

  const menuItems = [
    { icon: UsersIcon, text: t('Dashboard.users') },
    { icon: ArrowRightFromLineIcon, text: t('Dashboard.accessChat') },
  ];

  const positionOptions = ['Todos', 'Funcionário', 'Gestor', 'Main-admin'];

  useEffect(() => {
    if (!loading && !user) {
      router.push(`/${locale}/login`);
    }
  }, [user, loading, router, locale]);

  useEffect(() => {
    const fetchUsers = async () => {
      if (!isInitialLoad) setDashboardLoading(true);
      try {
        const usersCollection = collection(db, 'Users');
        const userSnapshot = await getDocs(usersCollection);
        const userList: User[] = userSnapshot.docs.map((doc) => ({
          id: doc.id,
          name: doc.data().name || '',
          email: doc.data().email || '',
          position: doc.data().position || 'user',
          tokenKey: doc.data().tokenKey,
        }));
        const sortedUsers = userList.sort((a, b) => a.name.localeCompare(b.name));
        setUsers(sortedUsers);
        const filteredList =
          initialFilter === 'Todos'
            ? sortedUsers
            : sortedUsers.filter((user) => user.position === initialFilter);
        setFilteredUsers(filteredList);
        setSearchPosition(initialFilter);
      } catch (error) {
        console.error('Error fetching users:', error);
      } finally {
        setDashboardLoading(false);
        setIsInitialLoad(false);
      }
    };

    if (user) {
      fetchUsers();
    }
  }, [isInitialLoad, initialFilter, user]);

  useEffect(() => {
    const filtered = users.filter(
      (user) =>
        (user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          user.email.toLowerCase().includes(searchTerm.toLowerCase())) &&
        (searchPosition === 'Todos' || user.position === searchPosition)
    );
    setFilteredUsers(filtered);
    setCurrentPage(1);
  }, [searchTerm, searchPosition, users]);

  const updateUserPosition = async (userId: string, newPosition: string) => {
    try {
      const userRef = doc(db, 'Users', userId);
      await updateDoc(userRef, {
        position: newPosition,
      });

      setUsers(
        users.map((user) =>
          user.id === userId ? { ...user, position: newPosition } : user
        )
      );
      setEditingUser(null);
    } catch (error) {
      console.error('Erro ao atualizar a posição do usuário:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      sessionStorage.removeItem('authToken');
      sessionStorage.removeItem('userRole');
      router.push(`/${locale}/login`);
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
    }
  };

  const handleChangeChat = async () => {
    const validLocales = ['en', 'pt', 'es'];
    const targetLocale = validLocales.includes(locale) ? locale : 'en';

    try {
      router.push(`/${targetLocale}/chat`);
    } catch (error) {
      console.error('Erro ao acessar o chat:', error);
    }
  };

  const renderContent = () => {
    switch (activeItem) {
      case t('Users'):
        return (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="mb-4 flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
              <div className="relative">
                <input
                  type="text"
                  name="searchTerm"
                  id="searchTerm"
                  className="w-full sm:w-64 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-black text-gray-900 transition duration-200 pl-10"
                  placeholder={t('Dashboard.searchPlaceholderIfExists', {
                    defaultMessage: 'Search users...',
                  })}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <SearchIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-500" />
              </div>
              <select
                id="searchPosition"
                name="searchPosition"
                className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-black text-gray-900 transition duration-200"
                value={searchPosition}
                onChange={(e) => {
                  setSearchPosition(e.target.value);
                  setInitialFilter(e.target.value);
                }}
              >
                {positionOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            {dashboardLoading ? (
              <p className="text-gray-700">
                {t('Dashboard.loadingUsersIfExists', { defaultMessage: 'Loading users...' })}
              </p>
            ) : (
              <>
                <table className="min-w-full divide-y divide-gray-300">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        {t('Dashboard.nameIfExists', { defaultMessage: 'Name' })}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        {t('Dashboard.emailIfExists', { defaultMessage: 'Email' })}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        {t('Dashboard.positionIfExists', { defaultMessage: 'Position' })}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider"></th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-300">
                    {filteredUsers
                      .slice((currentPage - 1) * 10, currentPage * 10)
                      .map((user) => (
                        <tr key={user.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {user.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {user.email}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <span
                              className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.position === 'Main-admin'
                                  ? 'bg-red-100 text-red-600'
                                  : user.position === 'Gestor'
                                  ? 'bg-blue-100 text-blue-600'
                                  : 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              {user.position}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="relative">
                              <button
                                onClick={() =>
                                  setEditingUser(editingUser === user.id ? null : user.id)
                                }
                                className="text-gray-500 hover:text-gray-900 transition-colors"
                              >
                                <MoreVerticalIcon className="h-5 w-5" />
                              </button>
                              {editingUser === user.id && (
                                <div className="absolute right-0 z-10 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-gray-300">
                                  <div
                                    className="py-1"
                                    role="menu"
                                    aria-orientation="vertical"
                                    aria-labelledby="options-menu"
                                  >
                                    {['Funcionário', 'Gestor', 'Main-admin'].map((position) => (
                                      <button
                                        key={position}
                                        onClick={() => updateUserPosition(user.id, position)}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-200 hover:text-gray-900"
                                        role="menuitem"
                                      >
                                        {position}
                                        {user.position === position && (
                                          <CheckIcon className="h-4 w-4 inline-block ml-2" />
                                        )}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              )}
                              </div>
                            </td>
                          </tr>
                        ))}
                  </tbody>
                </table>
                <div className="mt-4 flex justify-between">
                  <button
                    onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200 disabled:opacity-50"
                  >
                    {t('Dashboard.previousIfExists', { defaultMessage: 'Previous' })}
                  </button>
                  <button
                    onClick={() => setCurrentPage((prev) => prev + 1)}
                    disabled={currentPage * 10 >= filteredUsers.length}
                    className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200 disabled:opacity-50"
                  >
                    {t('Dashboard.nextIfExists', { defaultMessage: 'Next' })}
                  </button>
                </div>
              </>
            )}
          </div>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="text-gray-700">
        {t('Dashboard.loadingIfExists', { defaultMessage: 'Loading...' })}
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-gray-100 text-gray-900">
      <aside className="hidden md:flex flex-col w-64 bg-white shadow-lg">
        <div className="p-4">
          <h1 className="text-2xl font-bold text-gray-900">
            {t('Dashboard.adminPanelIfExists', { defaultMessage: 'Admin Panel' })}
          </h1>
        </div>
        <nav className="flex-1">
          <ul className="space-y-2 py-4">
            {menuItems.map((item) => (
              <MenuItem
                key={item.text}
                icon={item.icon}
                text={item.text}
                isActive={activeItem === item.text}
                onClick={() => {
                  setActiveItem(item.text);
                  if (item.text === t('Dashboard.accessChat')) {
                    handleChangeChat();
                  }
                }}
              />
            ))}
          </ul>
        </nav>
        <div className="p-6 mt-auto pt-8 border-t border-gray-300">
          <button
            onClick={handleLogout}
            className="flex items-center space-x-2 text-red-600 hover:text-red-700 transition-colors"
          >
            <LogOutIcon className="h-5 w-5" />
            <span>{t('Dashboard.logoutIfExists', { defaultMessage: 'Logout' })}</span>
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8 overflow-auto">
        <h2 className="text-3xl font-semibold mb-4 text-gray-900">{activeItem}</h2>
        {isInitialLoad ? (
          <p className="text-gray-700">
            {t('Dashboard.loadingInitialDataIfExists', { defaultMessage: 'Loading initial data...' })}
          </p>
        ) : activeItem === t('Users') ? (
          renderContent()
        ) : null}
      </main>
    </div>
  );
}