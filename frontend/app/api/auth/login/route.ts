import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { passcode } = await request.json();
    
    // In production, use env variables. For now, hardcode 'admin123' or use env.
    const validPasscode = process.env.ADMIN_PASSCODE || 'admin123';

    if (passcode === validPasscode) {
      const response = NextResponse.json({ success: true });
      
      // Set HttpOnly cookie
      response.cookies.set({
        name: 'admin_session',
        value: 'authenticated',
        httpOnly: true,
        path: '/',
        secure: process.env.NODE_ENV === 'production',
        maxAge: 60 * 60 * 24 * 7, // 1 week
      });
      
      return response;
    } else {
      return NextResponse.json({ success: false, message: 'Invalid passcode' }, { status: 401 });
    }
  } catch (e) {
    return NextResponse.json({ success: false }, { status: 500 });
  }
}
