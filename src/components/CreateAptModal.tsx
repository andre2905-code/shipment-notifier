import { X } from "lucide-react";
import { useState } from "react";
import { ApartmentType } from "../types";
import { createApartment } from "../services/api";
import { toast } from "sonner";

interface CreateAptModalProps {
  opened: boolean;
  onClose?: () => void;
  onSuccess?: () => void;
}

function CreateAptModal({ opened, onClose, onSuccess }: CreateAptModalProps) {
  if (!opened) return null;

  const [formData, setFormData] = useState<ApartmentType>({
    nome: "",
    email: "",
    bloco: "",
    apartamento: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!formData.nome || !formData.email || !formData.bloco || !formData.apartamento) {
      toast.error("Por favor, preencha todos os campos.");
      return;
    }

    createApartment(formData)
      .then((response) => {
        toast.success(`Apartamento ${formData.apartamento} criado com sucesso!`);
        console.log("Apartamento criado com sucesso:", response);
        if (onSuccess) onSuccess();
      })
      .catch((error) => {
        console.error("Error creating apartment:", error);
        toast.error("Ocorreu um erro ao criar o apartamento. Tente novamente.");
      });

    console.log("Form data:", formData);
  }

  return (
    <div className="backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>NOVO APARTAMENTO</h3>
          <button className="close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <label>
            Nome
            <input type="text" name="nome" value={formData.nome} onChange={handleChange} />
          </label>
          <label>
            Email
            <input type="email" name="email" value={formData.email} onChange={handleChange} />
          </label>
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

export default CreateAptModal;