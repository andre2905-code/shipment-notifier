import Blocks from './pages/Blocks'
import './App.css'
import Notifications from './pages/Notifications';
import Apartments from './pages/Apartments';

interface AppProps {
  resource: string;
}

function App({ resource }: AppProps) {

  return (
    <main>
      {resource == "blocos" && (
        <Blocks />
      )}
      {resource == "/" && (
        <Apartments />
      )}
      {resource == "notificacoes" && (
        <Notifications />
      )}
    </main>
  )
}

export default App;
