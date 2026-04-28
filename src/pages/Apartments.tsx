import { Plus } from "lucide-react";

const apts = [
  // {
  //   id: 1,
  //   ape_numero: "101",
  //   block: "Bloco A",
  //   inquilino: "João Silva",
  //   telefone: "(11) 92345-6789",
  // },
  // {
  //   id: 2,
  //   ape_numero: "102",
  //   block: "Bloco A",
  //   inquilino: "Maria Oliveira",
  //   telefone: "(11) 98765-4321",
  // },
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
          <h3>Apartamento {apt.ape_numero} - {apt.block}</h3>
          <p>Inquilino: {apt.inquilino}</p>
          <p>Telefone: {apt.telefone}</p>
        </div>
      ))}
    </section>
  );
};

export default Apartments;
