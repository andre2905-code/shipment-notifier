import { Building2, House, Building, Bell } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const Header = () => {
  const location = useLocation();
  const links = [
    { name: "Apartamentos", path: "/", icon: House },
    { name: "Blocos", path: "/blocos", icon: Building },
    { name: "Notificações", path: "/notificacoes", icon: Bell },
  ];
  return (
    <div className="menu">
      <header>
        <div className="header-content">
          <Building2 size={32} className="header-icon" />
          <div className="header-title">
            <h1>Residencial Aires</h1>
            <small>Sistema de Notificações de Entrega</small>
          </div>
        </div>
      </header>

      <nav>
        {links.map((link) => (
          <Link key={link.path} className={`nav-link ${location.pathname === link.path ? "active" : ""}`} to={link.path}>
            <link.icon size={20} className="nav-icon" />
            <span>{link.name}</span>
          </Link>
        ))}
        {/* <Link className="nav-link active" to="/">
          Apartamentos
        </Link>
        <Link className="nav-link" to="/blocos">
          Blocos
        </Link>
        <Link className="nav-link" to="/notificacoes">
          Notificações
        </Link> */}
      </nav>
    </div>
  );
};

export default Header;
