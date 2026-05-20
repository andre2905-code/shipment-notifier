import React from 'react';
import { NotificationType } from '../types';
import { Check, Plus, X } from "lucide-react";
import { fetchNotifications, updateNotificationStatus } from '../services/api';
import CreateNotificationsModal from '../components/CreateNotificationModal';
import { toast } from 'sonner';

const Notifications = () => {
  const [notifications, setNotifications] = React.useState<NotificationType[]>([]);
  const [showCreateModal, setShowCreateModal] = React.useState(false);
  const [showRetiradaModal, setShowRetiradaModal] = React.useState(false);
  const [retiradaCode, setRetiradaCode] = React.useState("");
  const [selectedNotificationId, setSelectedNotificationId] = React.useState<number | null>(null);

  const loadNotifications = () => {
    fetchNotifications()
      .then((data) => setNotifications(data.encomendas))
      .catch((error) => console.error("Error fetching notifications:", error));
  };

  React.useEffect(() => {
    loadNotifications();
  }, []);

  const handleCheckClick = (id: number) => {
    setSelectedNotificationId(id);
    setRetiradaCode("");
    setShowRetiradaModal(true);
  };

  const handleRetiradaSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!retiradaCode.trim()) {
      toast.error("Por favor, insira o código de retirada.");
      return;
    }

    updateNotificationStatus(retiradaCode)
      .then((response) => {
        console.log("Status atualizado com sucesso:", response);
        toast.success("Encomenda marcada como entregue!");

        loadNotifications();

        setShowRetiradaModal(false);
        setRetiradaCode("");
        setSelectedNotificationId(null);
      })
      .catch((error) => {
        console.error("Error updating notification status:", error);
        toast.error("Erro ao atualizar status da notificação!");
      });
  };

  return (
    <section className="notifications">
      <div className="section-heading">
        <h2>NOTIFICAÇÕES</h2>
        <button className="add-button" onClick={() => setShowCreateModal(true)}>
          <Plus size={16} />
          <span>Cadastrar</span>
        </button>
      </div>
      {notifications.length === 0 ? (
        <div className="no-results">
          <p>Nenhuma notificação encontrada.</p>
        </div>
      ) : notifications.map((notification) => (
        <div key={notification.id} className={`notification-card ${notification.status === "PENDENTE" ? "pending" : "delivered"}`}>
          <h3>Apartamento {notification.morador.apartamento}, Bloco {notification.morador.bloco} - {notification.morador.nome}</h3>
          <p><strong>Status:</strong> {notification.status}</p>

          <button className="check-button" onClick={() => handleCheckClick(notification.id)}>
            <Check size={ 16 } className='icon' />
          </button>
        </div>
      ))}

      {showCreateModal && (
        <CreateNotificationsModal
          opened={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            loadNotifications();
            setShowCreateModal(false);
          }}
        />
      )}

      {showRetiradaModal && (
        <div className="backdrop" onClick={() => setShowRetiradaModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>CÓDIGO DE RETIRADA</h3>
              <button className="close-button" onClick={() => setShowRetiradaModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleRetiradaSubmit}>
              <label>
                Código de Retirada
                <input 
                  type="text" 
                  value={retiradaCode} 
                  onChange={(e) => setRetiradaCode(e.target.value)} 
                  placeholder="Insira o código de retirada"
                  autoFocus
                />
              </label>
              <button type="submit">Confirmar</button>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}

export default Notifications;