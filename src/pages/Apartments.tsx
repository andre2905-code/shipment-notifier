import { Plus } from "lucide-react";
import { ApartmentType } from "../types";
import { useEffect, useState } from "react";
import { fetchApartments } from "../services/api";
import CreateAptModal from "../components/CreateAptModal";

const Apartments = () => {
  const [apts, setApts] = useState<ApartmentType[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const loadApartments = () => {
    fetchApartments()
      .then((data) => setApts(data.moradores))
      .catch((error) => console.error("Error fetching apartments:", error));
  };

  useEffect(() => {
    loadApartments();
  }, []);

  return (
    <section className="apartments">
      <div className="section-heading">
        <h2>APARTAMENTOS</h2>
        <button className="add-button" onClick={() => setShowCreateModal(true)}>
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
          <p><strong>Inquilino:</strong> {apt.nome}</p>
          <p><strong>Email:</strong> {apt.email}</p>
        </div>
      ))}
      {showCreateModal && (
        <CreateAptModal
          opened={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            loadApartments();
            setShowCreateModal(false);
          }}
        />
      )}
    </section>
  );
};

export default Apartments;
