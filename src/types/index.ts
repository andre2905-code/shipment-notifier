export interface ApartmentType = {
  id: number;
  nome: string;
  whatsapp: string;
  bloco: string;
  apartamento: string;
  status_validacao: string;
};

export interface NotificationType = {
  id: number;
  bloco: string;
  apartamento: string;
  status: "PENDENTE" | "ENTREGUE";
}
