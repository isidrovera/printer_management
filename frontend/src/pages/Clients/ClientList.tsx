// src/pages/Clients/ClientList.tsx
import React, { useEffect, useState } from "react";
import axios from "@/services/axiosInstance"; // Asegúrate de tener una instancia de Axios configurada

interface Client {
  id: number;
  name: string;
  status: string;
}

const ClientList = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const response = await axios.get<{ clients: Client[] }>("/clients");
        setClients(response.data.clients);
      } catch (err) {
        setError("Error al cargar los clientes");
      } finally {
        setLoading(false);
      }
    };

    fetchClients();
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Lista de Clientes</h1>

      {loading && <p>Cargando...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && (
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-2">ID</th>
              <th className="border p-2">Nombre</th>
              <th className="border p-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((client) => (
              <tr key={client.id} className="hover:bg-gray-50">
                <td className="border p-2 text-center">{client.id}</td>
                <td className="border p-2">{client.name}</td>
                <td className="border p-2">{client.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ClientList;
