import { X } from "lucide-react";
import { useState } from "react";
import { ApartmentType, NotificationType } from "../types";
import { createApartment, createNotification } from "../services/api";
import { toast } from "sonner";

interface CreateNotificationsModalProps {
  opened: boolean;
  onClose?: () => void;
  onSuccess?: () => void;
}

function CreateNotificationsModal({ opened, onClose, onSuccess }: CreateNotificationsModalProps) {
  if (!opened) return null;

  const [formData, setFormData] = useState<{
    bloco: string;
    apartamento: string;
    status: "PENDENTE" | "ENTREGUE";
  }>({
    bloco: "",
    apartamento: "",
    status: "PENDENTE"
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!formData.bloco || !formData.apartamento) {
      toast.error("Por favor, preencha todos os campos.");
      return;
    }

    createNotification(formData)
      .then((response) => {
        toast.success(`Notificação criada com sucesso!`);
        console.log("Notificação criada com sucesso:", response);
        if (onSuccess) onSuccess();
      })
      .catch((error) => {
        console.error("Error creating notification:", error);
        toast.error("Ocorreu um erro ao criar a notificação. Tente novamente.");
      });

    console.log("Form data:", formData);
  }

  return (
    <div className="backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>NOVA NOTIFICAÇÃO</h3>
          <button className="close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <label>
            Bloco
            <input type="text" name="bloco" value={formData.bloco} onChange={handleChange} />
          </label>
          <label>
            Apartamento
            <input type="text" name="apartamento" value={formData.apartamento} onChange={handleChange} />
          </label>
          <button type="submit">Criar</button>
        </form>
      </div>
    </div>
  );
}

export default CreateNotificationsModal;