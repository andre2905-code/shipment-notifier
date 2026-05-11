import { NotificationType } from './types';
import { Plus, Bell, MessageCircle } from "lucide-react";

const notifications: NotificationType[] = [
  {
    id: 1,
    bloco: "A",
    apartamento: "101",
    status: "PENDENTE",
  },
  {
    id: 2,
    bloco: "A",
    apartamento: "102",
    status: "ENTREGUE",
  },
];

const Notifications = () => {
  return (
    <section className="notifications">
      <div className="section-heading">
        <h2>NOTIFICAÇÕES</h2>
      </div>
      {notifications.length === 0 ? (
        <div className="no-results">
          <p>Nenhuma notificação encontrada.</p>
        </div>
      ) : notifications.map((notification) => (
        <div key={notification.id} className={`notification-card ${notification.status === "PENDENTE" ? "pending" : "delivered"}`}>
          <h3>Apartamento {notification.apartamento} - Bloco {notification.bloco}</h3>
          <p><strong>Status:</strong> {notification.status}</p>
          {notification.status === "PENDENTE" && (
            <a className="message-button" href={`https://wa.me/55?text=Olá,%20há%20uma%20encomenda%20aguardando.`}>
              <MessageCircle size={20} />
            </a>
          )}
        </div>
      ))}
    </section>
  );
}

export default Notifications;