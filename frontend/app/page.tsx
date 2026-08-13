import { cookies } from 'next/headers';
import RootClient from './RootClient';

export default async function Page() {
  const cookieStore = await cookies();
  const hasSessionCookie = cookieStore.get('syncsphere-session')?.value === 'active';

  return <RootClient hasSessionCookie={hasSessionCookie} />;
}
