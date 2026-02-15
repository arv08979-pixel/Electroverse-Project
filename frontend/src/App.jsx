import React, { useContext } from 'react'
import Player from './Player.jsx'
import './App.css'
import { AuthProvider } from './AuthContext.jsx'
import SignInCard from './sign in card.jsx'
import AuthContext from './AuthContext.jsx'

function InnerApp() {
  const { isAuthenticated, user, logout } = useContext(AuthContext);

  return (
    <div>
      <header style={{ padding: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontWeight: 'bold' }}>Electroverse</div>
        <nav>
          {isAuthenticated ? (
            <>
              <span style={{ marginRight: 12 }}>Hi {user?.username}</span>
              <button onClick={() => logout()}>Sign out</button>
            </>
          ) : null}
        </nav>
      </header>

      <main>
        {!isAuthenticated ? <SignInCard /> : <Player />}
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <InnerApp />
    </AuthProvider>
  )
}

export default App;