import { Plus } from "lucide-react";

type Apartment = {
  id: number;
  nome: string;
  whatsapp: string;
  bloco: string;
  apartamento: string;
  status_validacao: string;
};

const apts = [
  {
    id: 1,
    nome: "João Silva",
    whatsapp: "+5511923456789",
    bloco: "Bloco A",
    apartamento: "101",
    status_validacao: "PENDENTE",
  },
  {
    id: 2,
    nome: "Maria Oliveira",
    whatsapp: "+5511987654321",
    bloco: "Bloco A",
    apartamento: "102",
    status_validacao: "PENDENTE",
  },
]

const Apartments = () => {
  return (
    <section className="apartments">
      <div className="section-heading">
        <h2>APARTAMENTOS</h2>
        <button className="add-button">
          <Plus size={16} />
          <span>Cadastrar</span>
        </button>
      </div>
      {apts.length === 0 ? (
        <div className="no-results">
          <p>Nenhum apartamento cadastrado.</p>
        </div>
      ) : apts.map((apt) => (
        <div key={apt.id} className="apartment-card">
          <h3>Apartamento {apt.apartamento} - {apt.bloco}</h3>
          <p>Inquilino: {apt.nome}</p>
          <p>Telefone: {apt.whatsapp}</p>
        </div>
      ))}
    </section>
  );
};

export default Apartments;
