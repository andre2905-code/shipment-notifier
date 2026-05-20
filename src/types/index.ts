export interface ApartmentType {
  id?: number;
  nome: string;
  email: string;
  bloco: string;
  apartamento: string;
};

export interface NotificationType {
  id: number;
  bloco: string;
  apartamento: string;
  status: "PENDENTE" | "ENTREGUE";
  morador: {
    nome: string;
    bloco: string;
    apartamento: string;
  };
}
